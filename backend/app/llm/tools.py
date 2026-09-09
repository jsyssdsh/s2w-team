"""Tool (function-calling) definitions and shared execution helper for the chat assistant.

Tool schemas are owned here so both the real LLM path (service.py) and the
mock path (mock.py) invoke the exact same executor contract. The actual
execution functions (DB writes, matching logic, etc.) are injected by the
backend at call time -- this module never touches the database or SQL.
"""

from collections.abc import Awaitable, Callable
from typing import Any

from .models import ToolCallOutcome

# Backend-supplied async function that performs one tool's real work and
# returns a JSON-serializable result dict. Keyed by tool name in a dict the
# backend passes into run_chat_assistant / mock_chat.
ToolExecutor = Callable[..., Awaitable[dict[str, Any]]]

CHAT_TOOLS: list[dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "create_trade_request",
            "description": "농가와 도매처(또는 판매처) 사이에 새 거래 요청을 생성한다.",
            "parameters": {
                "type": "object",
                "properties": {
                    "crop_name": {"type": "string", "description": "품목명"},
                    "quantity_kg": {"type": "number", "description": "거래 요청 물량(kg)"},
                    "counterparty_name": {
                        "type": "string",
                        "description": "상대방(도매처/판매처) 이름",
                    },
                    "proposed_price_per_kg": {
                        "type": "number",
                        "description": "제안 단가(원/kg), 모르면 생략",
                    },
                    "note": {"type": "string", "description": "요청 메모, 없으면 생략"},
                },
                "required": ["crop_name", "quantity_kg", "counterparty_name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_trade_requests",
            "description": "현재 사용자와 관련된 거래 요청 목록을 조회한다.",
            "parameters": {
                "type": "object",
                "properties": {
                    "status": {
                        "type": "string",
                        "enum": ["pending", "accepted", "rejected", "completed"],
                        "description": "상태로 필터링, 없으면 전체 조회",
                    },
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "update_trade_request_status",
            "description": "거래 요청의 상태를 변경한다 (수락/거절/완료 처리).",
            "parameters": {
                "type": "object",
                "properties": {
                    "request_id": {"type": "string", "description": "거래 요청 ID"},
                    "status": {
                        "type": "string",
                        "enum": ["accepted", "rejected", "completed"],
                        "description": "변경할 상태",
                    },
                },
                "required": ["request_id", "status"],
            },
        },
    },
]


async def execute_tool_call(
    name: str, arguments: dict[str, Any], tool_executors: dict[str, ToolExecutor]
) -> ToolCallOutcome:
    """Run one tool invocation against the backend-injected executors.

    Never raises: a missing executor or an executor exception both come back
    as `error` on the outcome, so the chat loop can report them (or feed them
    back to the LLM as a tool result) instead of crashing the whole request.
    """
    executor = tool_executors.get(name)
    if executor is None:
        return ToolCallOutcome(
            name=name, arguments=arguments, error=f"No executor registered for tool '{name}'"
        )
    try:
        result = await executor(**arguments)
        return ToolCallOutcome(name=name, arguments=arguments, result=result)
    except Exception as exc:
        return ToolCallOutcome(name=name, arguments=arguments, error=str(exc))
