"""SPEC 5.3 -- 도매처 맞춤 판매처 연계 (등급별 판매처 매칭).

The grade -> retailer_type mapping is fixed by the spec's own example table
(특상품 -> 대형마트, 상품 -> 학교급식, 규격외 -> 가공업체, 판매기한임박 -> 지역음식점),
so it is a lookup table rather than a scored ranking. Matching a shipment lot
to an actual retailer still needs DB-fetched candidates (a retailer_type
alone isn't a retailer id), so this module only decides *which type* a lot
should go to and leaves picking the specific retailer row to the route.
"""

from __future__ import annotations

from dataclasses import dataclass

# Mirrors app.db.SHIPMENT_GRADES -> app.db.RETAILER_TYPES.
GRADE_TO_RETAILER_TYPE: dict[str, str] = {
    "특상품": "대형마트",
    "상품": "학교급식",
    "규격외": "가공업체",
    "판매기한임박": "지역음식점",
}

_GRADE_REASON: dict[str, str] = {
    "특상품": "외관과 크기가 균일한 특상품이라 대형마트 진열 규격에 적합합니다.",
    "상품": "대용량 안정 공급이 가능한 상품 등급이라 학교급식 납품에 적합합니다.",
    "규격외": "품질은 정상이나 모양이 불규칙해 가공 원료로 적합합니다.",
    "판매기한임박": "판매기한이 임박해 신속한 소진이 가능한 지역음식점에 적합합니다.",
}


@dataclass(frozen=True, slots=True)
class ShipmentLot:
    """One graded batch of produce awaiting a buyer match."""

    shipment_plan_id: str
    grade: str
    quantity_kg: float


@dataclass(frozen=True, slots=True)
class LotMatch:
    shipment_plan_id: str
    grade: str
    quantity_kg: float
    recommended_retailer_type: str
    reason: str


def match_lots_to_retailer_types(lots: list[ShipmentLot]) -> list[LotMatch]:
    """Assign each lot the retailer type its grade maps to.

    Raises ValueError on an unknown grade rather than silently defaulting --
    an unmapped grade means the shipment_plans row violates the CHECK
    constraint in db/schema.sql and should never reach this function.
    """
    matches: list[LotMatch] = []
    for lot in lots:
        retailer_type = GRADE_TO_RETAILER_TYPE.get(lot.grade)
        if retailer_type is None:
            raise ValueError(f"Unknown shipment grade: {lot.grade!r}")
        matches.append(
            LotMatch(
                shipment_plan_id=lot.shipment_plan_id,
                grade=lot.grade,
                quantity_kg=lot.quantity_kg,
                recommended_retailer_type=retailer_type,
                reason=_GRADE_REASON[lot.grade],
            )
        )
    return matches
