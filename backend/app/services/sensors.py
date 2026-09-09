"""SPEC 5.5 -- 스마트팜 재배환경 통합관리 (센서 기준값 비교 및 자동제어 판단).

Compares one sensor reading against a crop's crop_optimal_ranges row
(app.db.get_crop_optimal_ranges) and decides whether an actuator should run.
Ranges are half-open where the spec only defines a floor (light has no
max_value, per db/schema.sql's comment), matching SPEC 5.5's "조도: 설정 기준
이상".
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

SensorStatus = Literal["정상", "기준미달", "기준초과"]

# metric -> (below-range actuator, above-range actuator). None means that
# direction has no actuator response (e.g. light only has a floor to raise).
_ACTUATOR_BY_METRIC: dict[str, tuple[str | None, str | None]] = {
    "temperature": ("난방 작동", "환기 작동"),
    "humidity": ("가습 작동", "제습/환기 작동"),
    "soil_moisture": ("워터펌프 급수 시작", "급수 중단"),
    "light": ("조명 작동", None),
}


@dataclass(frozen=True, slots=True)
class SensorEvaluation:
    metric: str
    value: float
    min_value: float | None
    max_value: float | None
    status: SensorStatus
    control_action: str | None


def evaluate_sensor_reading(
    metric: str, value: float, min_value: float | None, max_value: float | None
) -> SensorEvaluation:
    """Classify one reading and decide whether an actuator should engage."""
    below_actuator, above_actuator = _ACTUATOR_BY_METRIC.get(metric, (None, None))

    if min_value is not None and value < min_value:
        return SensorEvaluation(metric, value, min_value, max_value, "기준미달", below_actuator)
    if max_value is not None and value > max_value:
        return SensorEvaluation(metric, value, min_value, max_value, "기준초과", above_actuator)
    return SensorEvaluation(metric, value, min_value, max_value, "정상", None)


def evaluate_latest_readings(
    readings: dict[str, float], ranges: dict[str, tuple[float | None, float | None]]
) -> list[SensorEvaluation]:
    """Evaluate every metric present in both `readings` and `ranges`.

    readings: {metric: value}. ranges: {metric: (min_value, max_value)}.
    Metrics missing a defined range are skipped -- there is nothing to compare
    against, so no control decision can be made.
    """
    results = []
    for metric, value in readings.items():
        if metric not in ranges:
            continue
        min_value, max_value = ranges[metric]
        results.append(evaluate_sensor_reading(metric, value, min_value, max_value))
    return results
