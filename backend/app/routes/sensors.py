"""Smart-farm sensor ingest and auto-control evaluation (SPEC 5.5)."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.db import (
    SENSOR_METRICS,
    get_crop_optimal_ranges,
    get_latest_sensor_readings,
    get_sensor_readings_range,
    get_smart_farm,
    insert_sensor_reading,
)
from app.services.sensors import SensorEvaluation, evaluate_latest_readings

router = APIRouter(prefix="/api/smart-farms", tags=["sensors"])


class SensorReadingIn(BaseModel):
    metric: str
    value: float
    unit: str
    measured_at: str | None = None


class SensorEvaluationOut(BaseModel):
    metric: str
    value: float
    min_value: float | None
    max_value: float | None
    status: str
    control_action: str | None


def _to_evaluation_out(e: SensorEvaluation) -> SensorEvaluationOut:
    return SensorEvaluationOut(
        metric=e.metric, value=e.value, min_value=e.min_value, max_value=e.max_value,
        status=e.status, control_action=e.control_action,
    )


@router.post("/{smart_farm_id}/sensors", response_model=SensorEvaluationOut, status_code=201)
async def ingest_sensor_reading(smart_farm_id: str, body: SensorReadingIn, crop_id: str | None = None) -> SensorEvaluationOut:
    """Record one reading (from the ESP32 edge controller) and evaluate it.

    crop_id is optional: without it we cannot look up an optimal range, so
    the reading is still recorded but evaluated as always-in-range (status
    "정상", no control_action) rather than guessing a range.
    """
    if body.metric not in SENSOR_METRICS:
        raise HTTPException(status_code=400, detail=f"Unknown metric: {body.metric}")

    farm = await get_smart_farm(smart_farm_id)
    if farm is None:
        raise HTTPException(status_code=404, detail=f"Smart farm {smart_farm_id} not found")

    await insert_sensor_reading(
        smart_farm_id=smart_farm_id,
        metric=body.metric,
        value=body.value,
        unit=body.unit,
        measured_at=body.measured_at,
    )

    if crop_id is None:
        return SensorEvaluationOut(
            metric=body.metric, value=body.value, min_value=None, max_value=None,
            status="정상", control_action=None,
        )

    ranges = await get_crop_optimal_ranges(crop_id)
    range_row = next((r for r in ranges if r["metric"] == body.metric), None)
    if range_row is None:
        return SensorEvaluationOut(
            metric=body.metric, value=body.value, min_value=None, max_value=None,
            status="정상", control_action=None,
        )

    [evaluation] = evaluate_latest_readings(
        {body.metric: body.value}, {body.metric: (range_row["min_value"], range_row["max_value"])}
    )
    return _to_evaluation_out(evaluation)


@router.get("/{smart_farm_id}/sensors/latest", response_model=list[SensorEvaluationOut])
async def get_latest_readings(smart_farm_id: str, crop_id: str | None = None) -> list[SensorEvaluationOut]:
    farm = await get_smart_farm(smart_farm_id)
    if farm is None:
        raise HTTPException(status_code=404, detail=f"Smart farm {smart_farm_id} not found")

    readings = await get_latest_sensor_readings(smart_farm_id)
    if not readings:
        return []

    if crop_id is None:
        return [
            SensorEvaluationOut(
                metric=metric, value=row["value"], min_value=None, max_value=None,
                status="정상", control_action=None,
            )
            for metric, row in readings.items()
        ]

    ranges = await get_crop_optimal_ranges(crop_id)
    range_by_metric = {r["metric"]: (r["min_value"], r["max_value"]) for r in ranges}
    values = {metric: row["value"] for metric, row in readings.items()}
    evaluations = evaluate_latest_readings(values, range_by_metric)
    return [_to_evaluation_out(e) for e in evaluations]


@router.get("/{smart_farm_id}/sensors/history")
async def get_sensor_history(smart_farm_id: str, metric: str, start: str, end: str) -> list[dict]:
    if metric not in SENSOR_METRICS:
        raise HTTPException(status_code=400, detail=f"Unknown metric: {metric}")
    return await get_sensor_readings_range(smart_farm_id, metric, start, end)
