"""Trade requests / transactions between a farmer's shipment plan and a
wholesaler or retailer.

net_profit_krw uses the same formula as app.services.wholesaler (판매금액 -
운송비 - 수수료) so a confirmed transaction's recorded profit is consistent
with the recommendation numbers that led to it.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, model_validator

from app.db import (
    TRANSACTION_STATUSES,
    create_transaction,
    get_shipment_plan,
    get_transaction,
    list_transactions_for_shipment,
    update_transaction_status,
)

router = APIRouter(prefix="/api/transactions", tags=["transactions"])


class TransactionCreateRequest(BaseModel):
    shipment_plan_id: str
    counterparty_type: str  # "wholesaler" | "retailer"
    quantity_kg: float
    unit_price_krw_per_kg: int
    wholesaler_id: str | None = None
    retailer_id: str | None = None
    recommendation_id: str | None = None
    transport_cost_krw: int = 0
    commission_rate: float = 0.0

    @model_validator(mode="after")
    def _counterparty_id_matches_type(self) -> "TransactionCreateRequest":
        if self.counterparty_type == "wholesaler" and not self.wholesaler_id:
            raise ValueError("wholesaler_id is required when counterparty_type is 'wholesaler'")
        if self.counterparty_type == "retailer" and not self.retailer_id:
            raise ValueError("retailer_id is required when counterparty_type is 'retailer'")
        return self


class TransactionOut(BaseModel):
    id: str
    shipment_plan_id: str
    wholesaler_id: str | None
    retailer_id: str | None
    counterparty_type: str
    recommendation_id: str | None
    quantity_kg: float
    unit_price_krw_per_kg: int
    transport_cost_krw: int
    commission_krw: int
    net_profit_krw: int | None
    status: str
    requested_at: str
    updated_at: str


@router.post("", response_model=TransactionOut, status_code=201)
async def create_transaction_route(body: TransactionCreateRequest) -> TransactionOut:
    plan = await get_shipment_plan(body.shipment_plan_id)
    if plan is None:
        raise HTTPException(status_code=404, detail="Shipment plan not found")

    revenue = body.unit_price_krw_per_kg * body.quantity_kg
    commission_krw = round(revenue * body.commission_rate)
    net_profit_krw = round(revenue - body.transport_cost_krw - commission_krw)

    txn = await create_transaction(
        shipment_plan_id=body.shipment_plan_id,
        counterparty_type=body.counterparty_type,
        quantity_kg=body.quantity_kg,
        unit_price_krw_per_kg=body.unit_price_krw_per_kg,
        wholesaler_id=body.wholesaler_id,
        retailer_id=body.retailer_id,
        recommendation_id=body.recommendation_id,
        transport_cost_krw=body.transport_cost_krw,
        commission_krw=commission_krw,
        net_profit_krw=net_profit_krw,
    )
    return TransactionOut(**txn)


@router.get("", response_model=list[TransactionOut])
async def list_transactions_route(shipment_plan_id: str) -> list[TransactionOut]:
    txns = await list_transactions_for_shipment(shipment_plan_id)
    return [TransactionOut(**t) for t in txns]


class TransactionStatusUpdateRequest(BaseModel):
    status: str


@router.patch("/{transaction_id}/status", response_model=TransactionOut)
async def update_transaction_status_route(
    transaction_id: str, body: TransactionStatusUpdateRequest
) -> TransactionOut:
    if body.status not in TRANSACTION_STATUSES:
        raise HTTPException(status_code=400, detail=f"Invalid status: {body.status}")

    existing = await get_transaction(transaction_id)
    if existing is None:
        raise HTTPException(status_code=404, detail="Transaction not found")

    updated = await update_transaction_status(transaction_id, body.status)
    return TransactionOut(**updated)
