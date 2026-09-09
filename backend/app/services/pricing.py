"""SPEC 5.1 -- AI 농산물 시세 예측 (출하일별 예상 가격/매출 비교).

Forecasting a market-wide wholesale price is out of scope for a prototype
regression model; instead each candidate shipping date is priced from the
crop's recorded/projected market_prices row for that date (app.db.get_price_history
already carries projected near-future rows the same way it carries past
ones -- see db/seed.sql). This module's job is only the arithmetic derived
from that price: revenue, percent change vs. a baseline date, and a supply
label -- never the price itself.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class PricePoint:
    """One date's recorded/projected wholesale price for a crop."""

    date: str
    wholesale_price_krw_per_kg: float


@dataclass(frozen=True, slots=True)
class ShippingDateResult:
    date: str
    expected_wholesale_price_per_kg: float
    expected_revenue: float
    price_change_percent: float
    market_supply_condition: str


# Thresholds below this magnitude are reported as flat/"보통" supply rather
# than up/down, so tiny rounding noise in price history doesn't flip the label.
_FLAT_THRESHOLD_PERCENT = 0.5


def build_shipping_date_options(
    quantity_kg: float, baseline_price_krw_per_kg: float, candidates: list[PricePoint]
) -> list[ShippingDateResult]:
    """Compute revenue/change/supply-label for each candidate shipping date.

    baseline_price_krw_per_kg is the price the change_percent is measured
    against (typically the earliest/current candidate date's price).
    """
    if quantity_kg <= 0:
        raise ValueError("quantity_kg must be positive")
    if baseline_price_krw_per_kg <= 0:
        raise ValueError("baseline_price_krw_per_kg must be positive")

    results: list[ShippingDateResult] = []
    for point in candidates:
        change_percent = (
            (point.wholesale_price_krw_per_kg - baseline_price_krw_per_kg)
            / baseline_price_krw_per_kg
            * 100
        )

        if change_percent > _FLAT_THRESHOLD_PERCENT:
            supply_condition = "공급량 감소 예상"
        elif change_percent < -_FLAT_THRESHOLD_PERCENT:
            supply_condition = "공급량 증가 예상"
        else:
            supply_condition = "공급량 보통"

        results.append(
            ShippingDateResult(
                date=point.date,
                expected_wholesale_price_per_kg=point.wholesale_price_krw_per_kg,
                expected_revenue=point.wholesale_price_krw_per_kg * quantity_kg,
                price_change_percent=round(change_percent, 1),
                market_supply_condition=supply_condition,
            )
        )
    return results


def best_shipping_date(results: list[ShippingDateResult]) -> ShippingDateResult:
    """Pick the candidate with the highest expected revenue."""
    if not results:
        raise ValueError("results must not be empty")
    return max(results, key=lambda r: r.expected_revenue)
