"""SPEC 5.2 -- 농가 맞춤형 도매처 추천.

Net profit formula (from SPEC 5.2 / 6.2): 예상 순수익 = 판매금액 - 운송비 - 수수료.
A wholesaler's purchase_capacity_kg may be less than the farmer's shipment
quantity, in which case only the capacity amount is actually sold (see the
spec's wholesaler-C example: 800kg bought out of a 1,000kg lot).
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class WholesalerOfferInput:
    """One wholesaler's standing offer for a crop, as read from the DB.

    Field names mirror app.db.get_wholesaler_candidates() row keys so callers
    can build this directly from a DB row without renaming.
    """

    wholesaler_id: str
    wholesaler_name: str
    purchase_unit_price_krw_per_kg: float
    purchase_capacity_kg: float
    transport_cost_krw: float
    commission_rate: float = 0.0


@dataclass(frozen=True, slots=True)
class WholesalerOfferResult:
    """Net-profit calculation for one wholesaler, ranked against its peers."""

    wholesaler_id: str
    wholesaler_name: str
    purchase_unit_price_krw_per_kg: float
    sellable_quantity_kg: float
    revenue_krw: float
    transport_cost_krw: float
    commission_krw: float
    net_profit_krw: float
    rank: int


def rank_wholesaler_offers(
    shipment_quantity_kg: float, offers: list[WholesalerOfferInput]
) -> list[WholesalerOfferResult]:
    """Compute net profit per wholesaler offer and rank best-first.

    Best-first means highest net_profit_krw gets rank 1. Ties keep the
    order offers were given in (stable sort).
    """
    if shipment_quantity_kg <= 0:
        raise ValueError("shipment_quantity_kg must be positive")

    scored: list[WholesalerOfferResult] = []
    for offer in offers:
        sellable_kg = min(offer.purchase_capacity_kg, shipment_quantity_kg)
        revenue = offer.purchase_unit_price_krw_per_kg * sellable_kg
        commission = revenue * offer.commission_rate
        net_profit = revenue - offer.transport_cost_krw - commission

        scored.append(
            WholesalerOfferResult(
                wholesaler_id=offer.wholesaler_id,
                wholesaler_name=offer.wholesaler_name,
                purchase_unit_price_krw_per_kg=offer.purchase_unit_price_krw_per_kg,
                sellable_quantity_kg=sellable_kg,
                revenue_krw=revenue,
                transport_cost_krw=offer.transport_cost_krw,
                commission_krw=commission,
                net_profit_krw=net_profit,
                rank=0,  # placeholder, assigned below
            )
        )

    scored.sort(key=lambda r: r.net_profit_krw, reverse=True)
    return [
        WholesalerOfferResult(
            wholesaler_id=r.wholesaler_id,
            wholesaler_name=r.wholesaler_name,
            purchase_unit_price_krw_per_kg=r.purchase_unit_price_krw_per_kg,
            sellable_quantity_kg=r.sellable_quantity_kg,
            revenue_krw=r.revenue_krw,
            transport_cost_krw=r.transport_cost_krw,
            commission_krw=r.commission_krw,
            net_profit_krw=r.net_profit_krw,
            rank=i + 1,
        )
        for i, r in enumerate(scored)
    ]
