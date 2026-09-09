"""SPEC 5.6 -- 유휴농지 맞춤형 탐색 및 농업인 연결 (적합도 점수 산출).

SPEC 5.6's example table only gives ranks (1/2/3), not numeric scores
("Scores are an illustrative suitability score" per app.llm.models), so this
module is free to choose a scoring formula as long as it reproduces sensible
rankings. Water access is weighted heaviest because the spec's own farmland-C
example ranks last despite having the shortest wholesaler distance and a
competitive area, solely for lacking confirmed water access.
"""

from __future__ import annotations

from dataclasses import dataclass

# Weights sum to 1.0. Water access dominates because SPEC 5.6 treats it as a
# near-disqualifying factor (촬地 C 사례 참고), not just one input among many.
_WEIGHT_WATER = 0.35
_WEIGHT_COLD_STORAGE = 0.15
_WEIGHT_DISTANCE = 0.20
_WEIGHT_RENT = 0.15
_WEIGHT_AREA = 0.15

# Normalization scales -- distances/rents beyond these are floored to a 0 score
# rather than going negative, since a wildly-out-of-range candidate shouldn't
# be able to drag the weighted sum below what a merely-poor one would.
_DISTANCE_SCALE_KM = 50.0
_RENT_HEADROOM_FACTOR = 1.3  # rent up to 130% of budget still scores > 0

_COLD_STORAGE_SCORE = {"가능": 1.0, "제한적": 0.5}


@dataclass(frozen=True, slots=True)
class FarmlandCandidate:
    farmland_id: str
    name: str
    area_pyeong: float
    monthly_rent_krw: float
    has_water_access: bool
    cold_storage_access: str  # "가능" | "제한적" | anything else -> 0 score
    distance_to_wholesaler_km: float


@dataclass(frozen=True, slots=True)
class FarmlandScoreResult:
    farmland_id: str
    name: str
    area_pyeong: float
    monthly_rent_krw: float
    has_water_access: bool
    cold_storage_access: str
    distance_to_wholesaler_km: float
    suitability_score: float  # 0-100
    rank: int


def _clip01(value: float) -> float:
    return max(0.0, min(1.0, value))


def _score_one(
    candidate: FarmlandCandidate, desired_area_pyeong: float, budget_monthly_rent_krw: float
) -> float:
    water_score = 1.0 if candidate.has_water_access else 0.0
    cold_score = _COLD_STORAGE_SCORE.get(candidate.cold_storage_access, 0.0)
    distance_score = _clip01(1 - candidate.distance_to_wholesaler_km / _DISTANCE_SCALE_KM)

    rent_headroom = budget_monthly_rent_krw * _RENT_HEADROOM_FACTOR
    rent_score = _clip01(1 - candidate.monthly_rent_krw / rent_headroom) if rent_headroom > 0 else 0.0

    area_score = (
        _clip01(1 - abs(candidate.area_pyeong - desired_area_pyeong) / desired_area_pyeong)
        if desired_area_pyeong > 0
        else 0.0
    )

    return (
        _WEIGHT_WATER * water_score
        + _WEIGHT_COLD_STORAGE * cold_score
        + _WEIGHT_DISTANCE * distance_score
        + _WEIGHT_RENT * rent_score
        + _WEIGHT_AREA * area_score
    )


def rank_farmland_candidates(
    desired_area_pyeong: float,
    budget_monthly_rent_krw: float,
    candidates: list[FarmlandCandidate],
) -> list[FarmlandScoreResult]:
    """Score and rank farmland candidates best-first (highest score = rank 1)."""
    scored = [
        (c, _score_one(c, desired_area_pyeong, budget_monthly_rent_krw) * 100) for c in candidates
    ]
    scored.sort(key=lambda pair: pair[1], reverse=True)

    return [
        FarmlandScoreResult(
            farmland_id=c.farmland_id,
            name=c.name,
            area_pyeong=c.area_pyeong,
            monthly_rent_krw=c.monthly_rent_krw,
            has_water_access=c.has_water_access,
            cold_storage_access=c.cold_storage_access,
            distance_to_wholesaler_km=c.distance_to_wholesaler_km,
            suitability_score=round(score, 1),
            rank=i + 1,
        )
        for i, (c, score) in enumerate(scored)
    ]
