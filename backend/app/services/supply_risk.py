"""SPEC 5.4 -- 지역별 수급 위험 조기 알림.

Supply/demand totals themselves come from app.db.get_supply_demand_balance;
this module only classifies the risk level and splits any excess supply
across mitigation channels. The channel weights reproduce the exact split in
SPEC 5.4's onion example (12t/6t/7t/3t out of a 28t excess) as a reusable
policy ratio -- the spec gives no other derivation for how the excess should
be divided, so this is the closest thing to a documented default.
"""

from __future__ import annotations

from dataclasses import dataclass

KG_PER_TON = 1000.0

# Risk bands as a fraction of buyer demand. excess_supply_kg <= 0 means supply
# does not even cover demand, so there is no oversupply risk at all.
_CAUTION_THRESHOLD = 0.10  # >10% of demand in excess -> at least 주의
_DANGER_THRESHOLD = 0.20  # >20% of demand in excess -> 위험

# (channel name, share of excess volume) -- shares sum to 1.0 and reproduce
# SPEC 5.4's 12/6/7/3 (out of 28) ton split exactly.
_MITIGATION_POLICY: tuple[tuple[str, float], ...] = (
    ("식품가공업체 추가 연결", 12 / 28),
    ("학교급식 업체 추가 연결", 6 / 28),
    ("출하 시기 조정", 7 / 28),
    ("지역 공동판매 연계", 3 / 28),
)


@dataclass(frozen=True, slots=True)
class MitigationAction:
    channel: str
    processed_volume_ton: float


@dataclass(frozen=True, slots=True)
class SupplyRiskResult:
    farmer_planned_ton: float
    wholesaler_inventory_ton: float
    total_supply_ton: float
    buyer_demand_ton: float
    excess_supply_ton: float
    risk_level: str  # "안전" | "주의" | "위험"
    response_plan: list[MitigationAction]


def compute_supply_risk(
    farmer_planned_kg: float, wholesaler_inventory_kg: float, retailer_demand_kg: float
) -> SupplyRiskResult:
    total_supply_kg = farmer_planned_kg + wholesaler_inventory_kg
    excess_kg = total_supply_kg - retailer_demand_kg

    if excess_kg <= 0:
        risk_level = "안전"
    else:
        excess_ratio = excess_kg / retailer_demand_kg if retailer_demand_kg > 0 else float("inf")
        if excess_ratio > _DANGER_THRESHOLD:
            risk_level = "위험"
        elif excess_ratio > _CAUTION_THRESHOLD:
            risk_level = "주의"
        else:
            risk_level = "안전"

    response_plan: list[MitigationAction] = []
    if excess_kg > 0:
        response_plan = [
            MitigationAction(channel=channel, processed_volume_ton=round(excess_kg * share / KG_PER_TON, 1))
            for channel, share in _MITIGATION_POLICY
        ]

    return SupplyRiskResult(
        farmer_planned_ton=round(farmer_planned_kg / KG_PER_TON, 1),
        wholesaler_inventory_ton=round(wholesaler_inventory_kg / KG_PER_TON, 1),
        total_supply_ton=round(total_supply_kg / KG_PER_TON, 1),
        buyer_demand_ton=round(retailer_demand_kg / KG_PER_TON, 1),
        excess_supply_ton=round(excess_kg / KG_PER_TON, 1),
        risk_level=risk_level,
        response_plan=response_plan,
    )
