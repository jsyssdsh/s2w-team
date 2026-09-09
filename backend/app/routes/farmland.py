"""Idle farmland map/list, detail, and matching (SPEC 4.4, 4.5, 5.6)."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.db import (
    create_recommendation,
    get_farmland,
    get_latest_sensor_readings,
    get_smart_farm_by_farmland,
    search_farmlands,
)
from app.llm import FarmlandOption, LlmServiceError, recommend_farmland
from app.llm import FarmlandRequest as LlmFarmlandRequest
from app.services.farmland import FarmlandCandidate, rank_farmland_candidates

router = APIRouter(prefix="/api/farmlands", tags=["farmland"])

# DB only records water/cold-storage access as a yes/no flag (see
# db/schema.sql), while SPEC 5.6's example table uses a three-tier scale
# ("가능"/"제한적"/불가). We collapse to the two values the data actually
# supports; every seeded example only ever uses these two anyway.
_COLD_STORAGE_LABEL = {True: "가능", False: "제한적"}


class FarmlandOut(BaseModel):
    id: str
    owner_user_id: str
    address: str
    region: str | None
    latitude: float | None
    longitude: float | None
    area_pyeong: float
    monthly_rent_krw: int
    has_water_access: bool
    has_cold_storage_access: bool
    distance_to_wholesaler_km: float | None
    soil_status: str | None
    condition_grade: str
    status: str


def _to_farmland_out(row: dict) -> FarmlandOut:
    return FarmlandOut(
        id=row["id"],
        owner_user_id=row["owner_user_id"],
        address=row["address"],
        region=row["region"],
        latitude=row["latitude"],
        longitude=row["longitude"],
        area_pyeong=row["area_pyeong"],
        monthly_rent_krw=row["monthly_rent_krw"],
        has_water_access=bool(row["has_water_access"]),
        has_cold_storage_access=bool(row["has_cold_storage_access"]),
        distance_to_wholesaler_km=row["distance_to_wholesaler_km"],
        soil_status=row["soil_status"],
        condition_grade=row["condition_grade"],
        status=row["status"],
    )


@router.get("", response_model=list[FarmlandOut])
async def list_farmlands(
    region: str | None = None,
    status: str | None = None,
    min_area_pyeong: float | None = None,
    max_area_pyeong: float | None = None,
    max_monthly_rent_krw: int | None = None,
    require_water_access: bool | None = None,
    require_cold_storage_access: bool | None = None,
) -> list[FarmlandOut]:
    rows = await search_farmlands(
        min_area_pyeong=min_area_pyeong,
        max_area_pyeong=max_area_pyeong,
        max_monthly_rent_krw=max_monthly_rent_krw,
        require_water_access=require_water_access,
        require_cold_storage_access=require_cold_storage_access,
        region=region,
        status=status,
    )
    return [_to_farmland_out(r) for r in rows]


class SmartFarmSummary(BaseModel):
    id: str
    farm_type: str
    operation_start_date: str
    latest_sensor_readings: dict[str, float]


class FarmlandDetailOut(FarmlandOut):
    smart_farm: SmartFarmSummary | None


@router.get("/{farmland_id}", response_model=FarmlandDetailOut)
async def get_farmland_detail(farmland_id: str) -> FarmlandDetailOut:
    row = await get_farmland(farmland_id)
    if row is None:
        raise HTTPException(status_code=404, detail=f"Farmland {farmland_id} not found")

    smart_farm = await get_smart_farm_by_farmland(farmland_id)
    smart_farm_out = None
    if smart_farm is not None:
        readings = await get_latest_sensor_readings(smart_farm["id"])
        smart_farm_out = SmartFarmSummary(
            id=smart_farm["id"],
            farm_type=smart_farm["farm_type"],
            operation_start_date=smart_farm["operation_start_date"],
            latest_sensor_readings={m: r["value"] for m, r in readings.items()},
        )

    base = _to_farmland_out(row)
    return FarmlandDetailOut(**base.model_dump(), smart_farm=smart_farm_out)


# --- 5.6 Farmland recommendation -------------------------------------------


class FarmlandRecommendationRequest(BaseModel):
    user_id: str
    desired_crop: str
    desired_area_pyeong: float
    budget_monthly_rent_krw: float
    region: str | None = None


class FarmlandOptionOut(BaseModel):
    farmland_id: str
    address: str
    area_pyeong: float
    monthly_rent_krw: float
    has_water_access: bool
    cold_storage_access: str
    distance_to_wholesaler_km: float
    suitability_score: float
    rank: int
    explanation: str


class FarmlandRecommendationResponse(BaseModel):
    recommended_farmland_id: str
    recommendation_reason: str
    options: list[FarmlandOptionOut]


@router.post("/recommendation", response_model=FarmlandRecommendationResponse)
async def farmland_recommendation(body: FarmlandRecommendationRequest) -> FarmlandRecommendationResponse:
    candidates_rows = await search_farmlands(status="idle", region=body.region)
    if not candidates_rows:
        raise HTTPException(status_code=404, detail="No idle farmland available")

    candidates = [
        FarmlandCandidate(
            farmland_id=r["id"],
            name=r["address"],
            area_pyeong=r["area_pyeong"],
            monthly_rent_krw=r["monthly_rent_krw"],
            has_water_access=bool(r["has_water_access"]),
            cold_storage_access=_COLD_STORAGE_LABEL[bool(r["has_cold_storage_access"])],
            distance_to_wholesaler_km=r["distance_to_wholesaler_km"] or 0.0,
        )
        for r in candidates_rows
    ]
    results = rank_farmland_candidates(body.desired_area_pyeong, body.budget_monthly_rent_krw, candidates)

    options_input = [
        FarmlandOption(
            name=r.name,
            area_pyeong=r.area_pyeong,
            monthly_rent=r.monthly_rent_krw,
            water_access=r.has_water_access,
            cold_storage_access=r.cold_storage_access,
            distance_to_wholesaler_km=r.distance_to_wholesaler_km,
            rank=r.rank,
        )
        for r in results
    ]
    llm_request = LlmFarmlandRequest(
        desired_crop=body.desired_crop,
        desired_area_pyeong=body.desired_area_pyeong,
        budget_monthly_rent=body.budget_monthly_rent_krw,
    )

    try:
        explanation = await recommend_farmland(llm_request, options_input)
    except LlmServiceError as exc:
        raise HTTPException(status_code=502, detail="AI 농지 추천 생성에 실패했습니다") from exc

    for r in results:
        await create_recommendation(
            recommendation_type="farmland_match",
            subject_type="user",
            subject_id=body.user_id,
            target_type="farmland",
            target_id=r.farmland_id,
            score=r.suitability_score,
            rank=r.rank,
            rationale=f"적합도 {r.suitability_score}점, {r.rank}위",
        )

    explanation_by_name = {e.name: e.explanation for e in explanation.options}
    options_out = [
        FarmlandOptionOut(
            farmland_id=r.farmland_id,
            address=r.name,
            area_pyeong=r.area_pyeong,
            monthly_rent_krw=r.monthly_rent_krw,
            has_water_access=r.has_water_access,
            cold_storage_access=r.cold_storage_access,
            distance_to_wholesaler_km=r.distance_to_wholesaler_km,
            suitability_score=r.suitability_score,
            rank=r.rank,
            explanation=explanation_by_name.get(r.name, ""),
        )
        for r in results
    ]
    recommended_id = next(r.farmland_id for r in results if r.name == explanation.recommended_farmland)

    return FarmlandRecommendationResponse(
        recommended_farmland_id=recommended_id,
        recommendation_reason=explanation.recommendation_reason,
        options=options_out,
    )
