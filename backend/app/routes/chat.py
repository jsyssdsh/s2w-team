"""Chat assistant endpoint (SPEC 6.1 flow: 시세 질문, 유통 추천 설명, 거래 요청 tool call).

Two separate identifiers, deliberately not conflated:

- `session_id`: which chat thread this message belongs to. Client-generated
  (frontend mints a UUID and keeps it in localStorage), passed through as-is
  to app.db's chat_messages storage. This is thread isolation, not auth --
  its only job is keeping two browser tabs from reading each other's history.
- `user_id`: whose shipment plans/trades the tool executors act on. There is
  no auth/session system yet (SPEC 4.1 lists login as a future item), so this
  defaults to the seeded demo farmer.
"""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from app.aggregation import find_counterparty_by_name, find_farmer_shipment_plan_for_crop
from app.db import (
    create_transaction,
    get_chat_history,
    get_crop_by_name,
    get_shipment_plans_by_farmer,
    get_wholesaler_candidates,
    insert_chat_message,
    list_transactions_for_shipment,
    update_transaction_status,
)
from app.llm import ToolCallOutcome, ToolExecutor, run_chat_assistant

router = APIRouter(prefix="/api/chat", tags=["chat"])

_DEFAULT_USER_ID = "user-farmer-kim"
_DEFAULT_SESSION_ID = "default"  # matches app.db's insert_chat_message/get_chat_history default


def _build_tool_executors(user_id: str) -> dict[str, ToolExecutor]:
    """Bind the chat tool contracts in app.llm.tools.CHAT_TOOLS to real DB work
    for one user. A fresh dict is built per request since it closes over
    user_id -- these are cheap closures, not stateful objects."""

    async def create_trade_request(
        crop_name: str,
        quantity_kg: float,
        counterparty_name: str,
        proposed_price_per_kg: float | None = None,
        note: str | None = None,
    ) -> dict:
        crop = await get_crop_by_name(crop_name)
        if crop is None:
            raise ValueError(f"'{crop_name}' 작물을 찾을 수 없습니다")

        plan = await find_farmer_shipment_plan_for_crop(user_id, crop["id"])
        if plan is None:
            raise ValueError(f"{crop_name}에 대한 진행 중인 출하 계획을 찾을 수 없습니다")

        found = await find_counterparty_by_name(counterparty_name)
        if found is None:
            raise ValueError(f"'{counterparty_name}' 거래처를 찾을 수 없습니다")
        counterparty_type, counterparty = found

        unit_price = proposed_price_per_kg
        if unit_price is None and counterparty_type == "wholesaler":
            # No price named -- fall back to the wholesaler's own posted offer.
            offers = await get_wholesaler_candidates(crop["id"])
            own_offer = next((o for o in offers if o["wholesaler_id"] == counterparty["id"]), None)
            unit_price = own_offer["purchase_unit_price_krw_per_kg"] if own_offer else 0
        unit_price = unit_price or 0

        return await create_transaction(
            shipment_plan_id=plan["id"],
            counterparty_type=counterparty_type,
            quantity_kg=quantity_kg,
            unit_price_krw_per_kg=round(unit_price),
            wholesaler_id=counterparty["id"] if counterparty_type == "wholesaler" else None,
            retailer_id=counterparty["id"] if counterparty_type == "retailer" else None,
        )

    async def list_trade_requests(status: str | None = None) -> dict:
        plans = await get_shipment_plans_by_farmer(user_id)
        requests: list[dict] = []
        for plan in plans:
            requests.extend(await list_transactions_for_shipment(plan["id"]))
        if status is not None:
            requests = [r for r in requests if r["status"] == status]
        return {"requests": requests}

    async def update_trade_request_status(request_id: str, status: str) -> dict:
        updated = await update_transaction_status(request_id, status)
        if updated is None:
            raise ValueError(f"거래 요청 {request_id}를 찾을 수 없습니다")
        return updated

    return {
        "create_trade_request": create_trade_request,
        "list_trade_requests": list_trade_requests,
        "update_trade_request_status": update_trade_request_status,
    }


class ChatRequest(BaseModel):
    message: str
    session_id: str = _DEFAULT_SESSION_ID
    user_id: str = _DEFAULT_USER_ID


class ChatResponse(BaseModel):
    message: str
    tool_calls: list[ToolCallOutcome]
    session_id: str


@router.post("", response_model=ChatResponse)
async def chat(body: ChatRequest) -> ChatResponse:
    """Send a message to the AI assistant."""
    history = await get_chat_history(session_id=body.session_id)
    await insert_chat_message(role="user", content=body.message, session_id=body.session_id)

    tool_executors = _build_tool_executors(body.user_id)
    result = await run_chat_assistant(body.message, history, tool_executors)

    actions = [tc.model_dump() for tc in result.tool_calls] if result.tool_calls else None
    await insert_chat_message(
        role="assistant", content=result.message, actions=actions, session_id=body.session_id
    )

    return ChatResponse(message=result.message, tool_calls=result.tool_calls, session_id=body.session_id)


@router.get("/history", response_model=list[dict])
async def chat_history(session_id: str = _DEFAULT_SESSION_ID) -> list[dict]:
    """Get recent chat messages for one chat thread."""
    return await get_chat_history(session_id=session_id)
