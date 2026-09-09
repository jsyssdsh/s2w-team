"""LLM service layer for the produce distribution assistant.

Exposes typed async functions the backend calls from routes. Every function
here either (a) turns already-computed numbers into a structured natural
language explanation, or (b) drives the chat tool-calling loop. No function
in this module does ranking, net-profit, or supply/demand math -- that stays
in deterministic backend code; see the module docstring in models.py.
"""

import asyncio
import json
import logging
import os
from typing import TypeVar

from dotenv import load_dotenv
from litellm import completion
from pydantic import BaseModel

from . import mock
from .models import (
    BuyerRecommendation,
    ChatAssistantResult,
    FarmlandOption,
    FarmlandRecommendation,
    FarmlandRequest,
    PriceForecastExplanation,
    ProduceLot,
    ShippingDateOption,
    SupplyRiskAlert,
    SupplyRiskInput,
    ToolCallOutcome,
    WholesalerOption,
    WholesalerRecommendation,
)
from .prompts import (
    build_buyer_recommendation_messages,
    build_chat_messages,
    build_farmland_recommendation_messages,
    build_price_forecast_messages,
    build_supply_risk_messages,
    build_wholesaler_recommendation_messages,
)
from .tools import CHAT_TOOLS, ToolExecutor, execute_tool_call

load_dotenv()  # populates OPENROUTER_API_KEY from backend/.env if present

logger = logging.getLogger(__name__)

MODEL = "openrouter/openai/gpt-oss-120b"
EXTRA_BODY = {"provider": {"order": ["cerebras"]}}
_MAX_RETRIES = 2
_MAX_TOOL_ROUNDS = 3

_ModelT = TypeVar("_ModelT", bound=BaseModel)


class LlmServiceError(RuntimeError):
    """Raised when an LLM call fails after all retries are exhausted."""


def _is_mock_mode() -> bool:
    return os.environ.get("LLM_MOCK", "").lower() == "true"


async def _structured_completion(
    messages: list[dict[str, str]], response_model: type[_ModelT]
) -> _ModelT:
    """Call the LLM for one structured-output response, with retries.

    Runs the (synchronous) litellm call in a worker thread so it doesn't
    block the event loop the FastAPI route is running on.
    """
    last_exc: Exception | None = None
    for attempt in range(_MAX_RETRIES + 1):
        try:
            response = await asyncio.to_thread(
                completion,
                model=MODEL,
                messages=messages,
                response_format=response_model,
                reasoning_effort="low",
                extra_body=EXTRA_BODY,
            )
            content = response.choices[0].message.content
            return response_model.model_validate_json(content)
        except Exception as exc:  # network errors, malformed JSON, schema mismatch
            last_exc = exc
            logger.warning(
                "LLM structured call failed (attempt %d/%d): %s",
                attempt + 1,
                _MAX_RETRIES + 1,
                exc,
            )
    logger.error("LLM structured call exhausted retries", exc_info=last_exc)
    raise LlmServiceError(f"{response_model.__name__} call failed after retries") from last_exc


# ---------------------------------------------------------------------------
# 5.1 시세 예측 근거 설명 및 출하 시기 제안
# ---------------------------------------------------------------------------


async def explain_price_forecast(
    crop_name: str, options: list[ShippingDateOption]
) -> PriceForecastExplanation:
    if _is_mock_mode():
        return mock.mock_price_forecast(crop_name, options)
    messages = build_price_forecast_messages(crop_name, options)
    return await _structured_completion(messages, PriceForecastExplanation)


# ---------------------------------------------------------------------------
# 5.2 농가 맞춤형 도매처 추천
# ---------------------------------------------------------------------------


async def recommend_wholesaler(
    crop_name: str, options: list[WholesalerOption]
) -> WholesalerRecommendation:
    if _is_mock_mode():
        return mock.mock_wholesaler_recommendation(crop_name, options)
    messages = build_wholesaler_recommendation_messages(crop_name, options)
    return await _structured_completion(messages, WholesalerRecommendation)


# ---------------------------------------------------------------------------
# 5.3 도매처 맞춤 판매처 연계
# ---------------------------------------------------------------------------


async def recommend_buyers(lots: list[ProduceLot]) -> BuyerRecommendation:
    if _is_mock_mode():
        return mock.mock_buyer_recommendation(lots)
    messages = build_buyer_recommendation_messages(lots)
    return await _structured_completion(messages, BuyerRecommendation)


# ---------------------------------------------------------------------------
# 5.4 지역별 수급 위험 조기 알림
# ---------------------------------------------------------------------------


async def generate_supply_risk_alert(risk_input: SupplyRiskInput) -> SupplyRiskAlert:
    if _is_mock_mode():
        return mock.mock_supply_risk_alert(risk_input)
    messages = build_supply_risk_messages(risk_input)
    return await _structured_completion(messages, SupplyRiskAlert)


# ---------------------------------------------------------------------------
# 5.6 유휴농지 맞춤형 탐색 및 농업인 연결
# ---------------------------------------------------------------------------


async def recommend_farmland(
    request: FarmlandRequest, options: list[FarmlandOption]
) -> FarmlandRecommendation:
    if _is_mock_mode():
        return mock.mock_farmland_recommendation(request, options)
    messages = build_farmland_recommendation_messages(request, options)
    return await _structured_completion(messages, FarmlandRecommendation)


# ---------------------------------------------------------------------------
# 채팅 어시스턴트 (tool call 포함)
# ---------------------------------------------------------------------------

_CHAT_FALLBACK_MESSAGE = "죄송합니다, 요청을 처리하는 중 오류가 발생했습니다. 잠시 후 다시 시도해 주세요."


async def run_chat_assistant(
    user_message: str,
    history: list[dict[str, str]],
    tool_executors: dict[str, ToolExecutor],
    context: str | None = None,
) -> ChatAssistantResult:
    """Run one chat turn, executing any tools the model calls.

    `tool_executors` maps tool name (see tools.CHAT_TOOLS) to an async
    function the backend supplies that performs the real work (DB writes,
    matching, etc.) and returns a JSON-serializable result dict.
    """
    if _is_mock_mode():
        return await mock.mock_chat(user_message, context, tool_executors)

    messages = build_chat_messages(context, history, user_message)
    tool_outcomes: list[ToolCallOutcome] = []

    for _ in range(_MAX_TOOL_ROUNDS):
        try:
            response = await asyncio.to_thread(
                completion,
                model=MODEL,
                messages=messages,
                tools=CHAT_TOOLS,
                reasoning_effort="low",
                extra_body=EXTRA_BODY,
            )
        except Exception:
            logger.exception("Chat completion failed")
            return ChatAssistantResult(message=_CHAT_FALLBACK_MESSAGE, tool_calls=tool_outcomes)

        choice_message = response.choices[0].message
        raw_tool_calls = getattr(choice_message, "tool_calls", None)

        if not raw_tool_calls:
            return ChatAssistantResult(message=choice_message.content or "", tool_calls=tool_outcomes)

        # Preserve the assistant's tool-call turn so the follow-up call has
        # the full exchange, matching the OpenAI-style tool-calling protocol.
        messages.append(
            {
                "role": "assistant",
                "content": choice_message.content or "",
                "tool_calls": [
                    {
                        "id": call.id,
                        "type": "function",
                        "function": {
                            "name": call.function.name,
                            "arguments": call.function.arguments,
                        },
                    }
                    for call in raw_tool_calls
                ],
            }
        )

        for call in raw_tool_calls:
            try:
                arguments = json.loads(call.function.arguments or "{}")
            except json.JSONDecodeError as exc:
                outcome = ToolCallOutcome(
                    name=call.function.name, arguments={}, error=f"Invalid arguments JSON: {exc}"
                )
            else:
                outcome = await execute_tool_call(call.function.name, arguments, tool_executors)

            tool_outcomes.append(outcome)
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": call.id,
                    "content": json.dumps(
                        outcome.result if outcome.error is None else {"error": outcome.error},
                        ensure_ascii=False,
                    ),
                }
            )

    # Ran out of tool-call rounds: ask once more for a plain summary.
    try:
        response = await asyncio.to_thread(
            completion,
            model=MODEL,
            messages=messages,
            reasoning_effort="low",
            extra_body=EXTRA_BODY,
        )
        final_message = response.choices[0].message.content or ""
    except Exception:
        logger.exception("Chat completion failed on final summary")
        final_message = _CHAT_FALLBACK_MESSAGE

    return ChatAssistantResult(message=final_message, tool_calls=tool_outcomes)
