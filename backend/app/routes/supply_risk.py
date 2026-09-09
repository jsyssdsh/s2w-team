"""Regional supply/demand risk alerts (SPEC 5.4)."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.db import create_recommendation, get_crop_by_name, get_supply_demand_balance
from app.llm import LlmServiceError, ResponseOption, SupplyRiskInput, generate_supply_risk_alert
from app.services.supply_risk import compute_supply_risk

router = APIRouter(prefix="/api/supply-risk", tags=["supply-risk"])


class SupplyRiskRequest(BaseModel):
    crop_name: str
    region: str


class MitigationActionOut(BaseModel):
    channel: str
    processed_volume_ton: float
    rationale: str


class SupplyRiskResponse(BaseModel):
    region: str
    crop_name: str
    farmer_planned_ton: float
    wholesaler_inventory_ton: float
    total_supply_ton: float
    buyer_demand_ton: float
    excess_supply_ton: float
    risk_level: str
    alert_message: str
    situation_explanation: str
    response_plan: list[MitigationActionOut]


@router.post("", response_model=SupplyRiskResponse)
async def supply_risk(body: SupplyRiskRequest) -> SupplyRiskResponse:
    crop = await get_crop_by_name(body.crop_name)
    if crop is None:
        raise HTTPException(status_code=404, detail=f"Crop {body.crop_name!r} not found")

    balance = await get_supply_demand_balance(crop["id"], region=body.region)
    result = compute_supply_risk(
        farmer_planned_kg=balance["farmer_planned_kg"],
        wholesaler_inventory_kg=balance["wholesaler_inventory_kg"],
        retailer_demand_kg=balance["retailer_demand_kg"],
    )

    risk_input = SupplyRiskInput(
        region=body.region,
        crop_name=body.crop_name,
        farm_planned_shipment_ton=result.farmer_planned_ton,
        wholesaler_existing_stock_ton=result.wholesaler_inventory_ton,
        total_supply_ton=result.total_supply_ton,
        buyer_demand_ton=result.buyer_demand_ton,
        excess_supply_ton=result.excess_supply_ton,
        risk_level=result.risk_level,
        response_options=[
            ResponseOption(channel=a.channel, processed_volume_ton=a.processed_volume_ton)
            for a in result.response_plan
        ],
    )

    try:
        alert = await generate_supply_risk_alert(risk_input)
    except LlmServiceError as exc:
        raise HTTPException(status_code=502, detail="AI 수급 위험 경보 생성에 실패했습니다") from exc

    await create_recommendation(
        recommendation_type="supply_risk_alert",
        subject_type="crop",
        subject_id=crop["id"],
        target_type="region",
        target_id=body.region,
        score=-result.excess_supply_ton,
        rank=None,
        rationale=alert.alert_message,
        metadata={
            "farmer_planned_kg": balance["farmer_planned_kg"],
            "wholesaler_inventory_kg": balance["wholesaler_inventory_kg"],
            "total_supply_kg": balance["total_supply_kg"],
            "retailer_demand_kg": balance["retailer_demand_kg"],
            "excess_supply_kg": balance["excess_supply_kg"],
            "risk_level": result.risk_level,
        },
    )

    rationale_by_channel = {p.channel: p.rationale for p in alert.response_plan}
    response_plan = [
        MitigationActionOut(
            channel=a.channel,
            processed_volume_ton=a.processed_volume_ton,
            rationale=rationale_by_channel.get(a.channel, ""),
        )
        for a in result.response_plan
    ]

    return SupplyRiskResponse(
        region=body.region,
        crop_name=body.crop_name,
        farmer_planned_ton=result.farmer_planned_ton,
        wholesaler_inventory_ton=result.wholesaler_inventory_ton,
        total_supply_ton=result.total_supply_ton,
        buyer_demand_ton=result.buyer_demand_ton,
        excess_supply_ton=result.excess_supply_ton,
        risk_level=result.risk_level,
        alert_message=alert.alert_message,
        situation_explanation=alert.situation_explanation,
        response_plan=response_plan,
    )
