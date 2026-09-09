"""Farmer dashboard: shipment plans, price forecast (SPEC 5.1), wholesaler
recommendation (SPEC 5.2)."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.db import (
    create_recommendation,
    create_shipment_plan,
    get_crop,
    get_latest_sensor_readings,
    get_price_history,
    get_shipment_plan,
    get_shipment_plans_by_farmer,
    get_user,
    get_wholesaler_candidates,
    list_smart_farms,
)
from app.llm import (
    LlmServiceError,
    ShippingDateOption,
    WholesalerOption,
    explain_price_forecast,
    recommend_wholesaler,
)
from app.services.pricing import PricePoint, build_shipping_date_options
from app.services.wholesaler import WholesalerOfferInput, rank_wholesaler_offers

router = APIRouter(prefix="/api/farmer", tags=["farmer"])


# --- Shipment plans ----------------------------------------------------


class ShipmentPlanOut(BaseModel):
    id: str
    farmer_user_id: str
    smart_farm_id: str | None
    crop_id: str
    crop_name: str
    region: str | None
    expected_yield_kg: float
    planned_shipment_date: str
    grade: str
    status: str


class ShipmentPlanCreateRequest(BaseModel):
    farmer_user_id: str
    crop_id: str
    expected_yield_kg: float
    planned_shipment_date: str
    grade: str
    smart_farm_id: str | None = None
    region: str | None = None


async def _to_shipment_plan_out(plan: dict) -> ShipmentPlanOut:
    crop = await get_crop(plan["crop_id"])
    return ShipmentPlanOut(**plan, crop_name=crop["name"] if crop else plan["crop_id"])


@router.get("/{farmer_id}/shipment-plans", response_model=list[ShipmentPlanOut])
async def get_shipment_plans(farmer_id: str, status: str | None = None) -> list[ShipmentPlanOut]:
    plans = await get_shipment_plans_by_farmer(farmer_id, status=status)
    return [await _to_shipment_plan_out(p) for p in plans]


@router.post("/shipment-plans", response_model=ShipmentPlanOut, status_code=201)
async def create_shipment_plan_route(body: ShipmentPlanCreateRequest) -> ShipmentPlanOut:
    plan = await create_shipment_plan(
        farmer_user_id=body.farmer_user_id,
        crop_id=body.crop_id,
        expected_yield_kg=body.expected_yield_kg,
        planned_shipment_date=body.planned_shipment_date,
        grade=body.grade,
        smart_farm_id=body.smart_farm_id,
        region=body.region,
    )
    return await _to_shipment_plan_out(plan)


# --- Dashboard -----------------------------------------------------------


class SmartFarmOut(BaseModel):
    id: str
    farmland_id: str
    farm_type: str
    operation_start_date: str
    latest_sensor_readings: dict[str, float]


class FarmerDashboardOut(BaseModel):
    farmer_id: str
    farmer_name: str
    shipment_plans: list[ShipmentPlanOut]
    smart_farms: list[SmartFarmOut]


@router.get("/{farmer_id}/dashboard", response_model=FarmerDashboardOut)
async def get_farmer_dashboard(farmer_id: str) -> FarmerDashboardOut:
    farmer = await get_user(farmer_id)
    if farmer is None or farmer["role"] != "farmer":
        raise HTTPException(status_code=404, detail=f"Farmer {farmer_id} not found")

    plans = await get_shipment_plans_by_farmer(farmer_id, status="planned")
    plans_out = [await _to_shipment_plan_out(p) for p in plans]

    all_farms = await list_smart_farms()
    farms_out: list[SmartFarmOut] = []
    for farm in all_farms:
        if farm["farmer_user_id"] != farmer_id:
            continue
        readings = await get_latest_sensor_readings(farm["id"])
        farms_out.append(
            SmartFarmOut(
                id=farm["id"],
                farmland_id=farm["farmland_id"],
                farm_type=farm["farm_type"],
                operation_start_date=farm["operation_start_date"],
                latest_sensor_readings={m: r["value"] for m, r in readings.items()},
            )
        )

    return FarmerDashboardOut(
        farmer_id=farmer_id, farmer_name=farmer["name"], shipment_plans=plans_out, smart_farms=farms_out
    )


# --- 5.1 Price forecast ---------------------------------------------------


class PriceForecastRequest(BaseModel):
    shipment_plan_id: str
    candidate_dates: list[str] | None = None


class PriceForecastOptionOut(BaseModel):
    date: str
    expected_wholesale_price_per_kg: float
    expected_revenue: float
    price_change_percent: float
    market_supply_condition: str
    explanation: str
    system_guidance: str


class PriceForecastResponse(BaseModel):
    crop_name: str
    summary: str
    recommended_date: str
    recommendation_reason: str
    options: list[PriceForecastOptionOut]


@router.post("/price-forecast", response_model=PriceForecastResponse)
async def price_forecast(body: PriceForecastRequest) -> PriceForecastResponse:
    plan = await get_shipment_plan(body.shipment_plan_id)
    if plan is None:
        raise HTTPException(status_code=404, detail="Shipment plan not found")
    crop = await get_crop(plan["crop_id"])
    if crop is None:
        raise HTTPException(status_code=404, detail="Crop not found")

    history = await get_price_history(plan["crop_id"], region=plan.get("region"))
    if body.candidate_dates:
        chosen = [h for h in history if h["price_date"] in body.candidate_dates]
    else:
        chosen = history[-5:]  # most recent recorded/projected rows
    if not chosen:
        raise HTTPException(status_code=404, detail="No price history available for this crop")

    baseline_price = chosen[0]["wholesale_price_krw_per_kg"]
    points = [PricePoint(h["price_date"], h["wholesale_price_krw_per_kg"]) for h in chosen]
    results = build_shipping_date_options(plan["expected_yield_kg"], baseline_price, points)

    options_input = [
        ShippingDateOption(
            date=r.date,
            expected_wholesale_price_per_kg=r.expected_wholesale_price_per_kg,
            expected_revenue=r.expected_revenue,
            price_change_percent=r.price_change_percent,
            market_supply_condition=r.market_supply_condition,
        )
        for r in results
    ]

    try:
        explanation = await explain_price_forecast(crop["name"], options_input)
    except LlmServiceError as exc:
        raise HTTPException(status_code=502, detail="AI 시세 설명 생성에 실패했습니다") from exc

    for r in results:
        await create_recommendation(
            recommendation_type="price_forecast",
            subject_type="shipment_plan",
            subject_id=plan["id"],
            target_type="shipment_date",
            target_id=r.date,
            score=r.expected_revenue,
            rank=None,
            rationale=f"{r.market_supply_condition}, 예상 판매금액 {r.expected_revenue:,.0f}원",
            metadata={
                "price_krw_per_kg": r.expected_wholesale_price_per_kg,
                "change_percent_vs_base": r.price_change_percent,
                "market_outlook": r.market_supply_condition,
            },
        )

    advice_by_date = {a.date: a for a in explanation.options}
    merged = [
        PriceForecastOptionOut(
            date=r.date,
            expected_wholesale_price_per_kg=r.expected_wholesale_price_per_kg,
            expected_revenue=r.expected_revenue,
            price_change_percent=r.price_change_percent,
            market_supply_condition=r.market_supply_condition,
            explanation=advice_by_date[r.date].explanation if r.date in advice_by_date else "",
            system_guidance=(
                advice_by_date[r.date].system_guidance if r.date in advice_by_date else "즉시 출하 가능"
            ),
        )
        for r in results
    ]

    return PriceForecastResponse(
        crop_name=crop["name"],
        summary=explanation.summary,
        recommended_date=explanation.recommended_date,
        recommendation_reason=explanation.recommendation_reason,
        options=merged,
    )


# --- 5.2 Wholesaler recommendation ---------------------------------------


class WholesalerRecommendationRequest(BaseModel):
    shipment_plan_id: str


class WholesalerOptionOut(BaseModel):
    wholesaler_id: str
    wholesaler_name: str
    purchase_unit_price_krw_per_kg: float
    sellable_quantity_kg: float
    transport_cost_krw: float
    net_profit_krw: float
    rank: int
    explanation: str


class WholesalerRecommendationResponse(BaseModel):
    crop_name: str
    recommended_wholesaler: str
    recommendation_reason: str
    options: list[WholesalerOptionOut]


@router.post("/wholesaler-recommendation", response_model=WholesalerRecommendationResponse)
async def wholesaler_recommendation(body: WholesalerRecommendationRequest) -> WholesalerRecommendationResponse:
    plan = await get_shipment_plan(body.shipment_plan_id)
    if plan is None:
        raise HTTPException(status_code=404, detail="Shipment plan not found")
    crop = await get_crop(plan["crop_id"])
    if crop is None:
        raise HTTPException(status_code=404, detail="Crop not found")

    offers = await get_wholesaler_candidates(plan["crop_id"])
    if not offers:
        raise HTTPException(status_code=404, detail="No wholesaler offers available for this crop")

    offer_inputs = [
        WholesalerOfferInput(
            wholesaler_id=o["wholesaler_id"],
            wholesaler_name=o["wholesaler_name"],
            purchase_unit_price_krw_per_kg=o["purchase_unit_price_krw_per_kg"],
            purchase_capacity_kg=o["purchase_capacity_kg"],
            transport_cost_krw=o["transport_cost_krw"],
            commission_rate=o["commission_rate"],
        )
        for o in offers
    ]
    results = rank_wholesaler_offers(plan["expected_yield_kg"], offer_inputs)

    options_input = [
        WholesalerOption(
            name=r.wholesaler_name,
            purchase_price_per_kg=r.purchase_unit_price_krw_per_kg,
            purchase_quantity_kg=r.sellable_quantity_kg,
            transport_cost=r.transport_cost_krw,
            net_profit=r.net_profit_krw,
            rank=r.rank,
        )
        for r in results
    ]

    try:
        explanation = await recommend_wholesaler(crop["name"], options_input)
    except LlmServiceError as exc:
        raise HTTPException(status_code=502, detail="AI 도매처 추천 생성에 실패했습니다") from exc

    for r in results:
        await create_recommendation(
            recommendation_type="wholesaler_match",
            subject_type="shipment_plan",
            subject_id=plan["id"],
            target_type="wholesaler",
            target_id=r.wholesaler_id,
            score=r.net_profit_krw,
            rank=r.rank,
            rationale=f"순수익 {r.net_profit_krw:,.0f}원, {r.rank}위",
            metadata={
                "purchase_unit_price_krw_per_kg": r.purchase_unit_price_krw_per_kg,
                "quantity_kg": r.sellable_quantity_kg,
                "transport_cost_krw": r.transport_cost_krw,
                "commission_krw": r.commission_krw,
            },
        )

    explanation_by_name = {e.name: e.explanation for e in explanation.options}
    merged = [
        WholesalerOptionOut(
            wholesaler_id=r.wholesaler_id,
            wholesaler_name=r.wholesaler_name,
            purchase_unit_price_krw_per_kg=r.purchase_unit_price_krw_per_kg,
            sellable_quantity_kg=r.sellable_quantity_kg,
            transport_cost_krw=r.transport_cost_krw,
            net_profit_krw=r.net_profit_krw,
            rank=r.rank,
            explanation=explanation_by_name.get(r.wholesaler_name, ""),
        )
        for r in results
    ]

    return WholesalerRecommendationResponse(
        crop_name=crop["name"],
        recommended_wholesaler=explanation.recommended_wholesaler,
        recommendation_reason=explanation.recommendation_reason,
        options=merged,
    )
