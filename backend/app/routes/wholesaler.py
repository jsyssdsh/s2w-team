"""Wholesaler dashboard (SPEC 4.3) and buyer-type matching (SPEC 5.3)."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.db import (
    create_recommendation,
    get_retailer_candidates_for_grade,
    get_shipment_plan,
    get_wholesaler,
    get_wholesaler_candidates,
    list_crops,
    list_shipment_plans,
    list_wholesalers,
)
from app.llm import LlmServiceError, ProduceLot, recommend_buyers
from app.services.buyer_matching import ShipmentLot, match_lots_to_retailer_types

router = APIRouter(prefix="/api/wholesaler", tags=["wholesaler"])


# --- Dashboard -------------------------------------------------------------


class RecommendedFarmerShipment(BaseModel):
    shipment_plan_id: str
    farmer_user_id: str
    crop_name: str
    expected_yield_kg: float
    planned_shipment_date: str
    grade: str
    recommended_trade_price_krw_per_kg: float


class WholesalerDashboardOut(BaseModel):
    wholesaler_id: str
    wholesaler_name: str
    supply_available_count: int
    ai_recommended_count: int
    expected_amount_krw: float
    recommended_farmer_shipments: list[RecommendedFarmerShipment]


@router.get("/{wholesaler_id}/dashboard", response_model=WholesalerDashboardOut)
async def get_wholesaler_dashboard(wholesaler_id: str) -> WholesalerDashboardOut:
    wholesaler = await get_wholesaler(wholesaler_id)
    if wholesaler is None:
        raise HTTPException(status_code=404, detail=f"Wholesaler {wholesaler_id} not found")

    # A wholesaler's own crop_offers aren't fetchable by wholesaler_id directly
    # in app.db (offers are queried per-crop), so ask for candidates per crop
    # the platform tracks and keep only this wholesaler's own offer prices.
    recommended: list[RecommendedFarmerShipment] = []
    for crop in await list_crops():
        offers = await get_wholesaler_candidates(crop["id"])
        own_offer = next((o for o in offers if o["wholesaler_id"] == wholesaler_id), None)
        if own_offer is None:
            continue

        plans = await list_shipment_plans(
            crop_id=crop["id"], region=wholesaler.get("region"), status="planned"
        )
        plans.sort(key=lambda p: p["expected_yield_kg"], reverse=True)
        for plan in plans:
            recommended.append(
                RecommendedFarmerShipment(
                    shipment_plan_id=plan["id"],
                    farmer_user_id=plan["farmer_user_id"],
                    crop_name=crop["name"],
                    expected_yield_kg=plan["expected_yield_kg"],
                    planned_shipment_date=plan["planned_shipment_date"],
                    grade=plan["grade"],
                    recommended_trade_price_krw_per_kg=own_offer["purchase_unit_price_krw_per_kg"],
                )
            )

    expected_amount = sum(
        r.expected_yield_kg * r.recommended_trade_price_krw_per_kg for r in recommended
    )

    return WholesalerDashboardOut(
        wholesaler_id=wholesaler_id,
        wholesaler_name=wholesaler["name"],
        supply_available_count=len(recommended),
        ai_recommended_count=len(recommended),
        expected_amount_krw=round(expected_amount, 0),
        recommended_farmer_shipments=recommended,
    )


@router.get("", response_model=list[dict])
async def list_all_wholesalers(region: str | None = None) -> list[dict]:
    return await list_wholesalers(region=region)


# --- 5.3 Buyer-type recommendation -----------------------------------------


class BuyerRecommendationRequest(BaseModel):
    shipment_plan_ids: list[str]


class BuyerMatchOut(BaseModel):
    shipment_plan_id: str
    grade: str
    quantity_kg: float
    recommended_retailer_type: str
    matched_retailer_id: str | None
    matched_retailer_name: str | None
    reason: str


class BuyerRecommendationResponse(BaseModel):
    matches: list[BuyerMatchOut]


@router.post("/buyer-recommendation", response_model=BuyerRecommendationResponse)
async def buyer_recommendation(body: BuyerRecommendationRequest) -> BuyerRecommendationResponse:
    if not body.shipment_plan_ids:
        raise HTTPException(status_code=400, detail="shipment_plan_ids must not be empty")

    lots: list[ShipmentLot] = []
    plans_by_id: dict[str, dict] = {}
    for plan_id in body.shipment_plan_ids:
        plan = await get_shipment_plan(plan_id)
        if plan is None:
            raise HTTPException(status_code=404, detail=f"Shipment plan {plan_id} not found")
        plans_by_id[plan_id] = plan
        lots.append(ShipmentLot(plan_id, plan["grade"], plan["expected_yield_kg"]))

    type_matches = match_lots_to_retailer_types(lots)

    condition_notes = {
        "특상품": "외관과 크기가 균일함",
        "상품": "대용량 안정 공급 가능",
        "규격외": "품질은 정상이나 모양이 불규칙함",
        "판매기한임박": "신속한 판매 필요",
    }
    produce_lots = [
        ProduceLot(
            lot_id=m.shipment_plan_id,
            grade=m.grade,
            quantity_kg=m.quantity_kg,
            condition_note=condition_notes.get(m.grade, m.grade),
        )
        for m in type_matches
    ]

    try:
        llm_result = await recommend_buyers(produce_lots)
    except LlmServiceError as exc:
        raise HTTPException(status_code=502, detail="AI 판매처 추천 생성에 실패했습니다") from exc
    reason_by_lot = {m.lot_id: m.reason for m in llm_result.matches}

    matches: list[BuyerMatchOut] = []
    for m in type_matches:
        plan = plans_by_id[m.shipment_plan_id]
        candidates = await get_retailer_candidates_for_grade(plan["crop_id"], m.grade)
        best = candidates[0] if candidates else None

        await create_recommendation(
            recommendation_type="retailer_match",
            subject_type="shipment_plan",
            subject_id=m.shipment_plan_id,
            target_type="retailer",
            target_id=best["retailer_id"] if best else m.recommended_retailer_type,
            score=m.quantity_kg,
            rank=1,
            rationale=reason_by_lot.get(m.shipment_plan_id, m.reason),
        )

        matches.append(
            BuyerMatchOut(
                shipment_plan_id=m.shipment_plan_id,
                grade=m.grade,
                quantity_kg=m.quantity_kg,
                recommended_retailer_type=m.recommended_retailer_type,
                matched_retailer_id=best["retailer_id"] if best else None,
                matched_retailer_name=best["retailer_name"] if best else None,
                reason=reason_by_lot.get(m.shipment_plan_id, m.reason),
            )
        )

    return BuyerRecommendationResponse(matches=matches)
