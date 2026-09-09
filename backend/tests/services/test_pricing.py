"""Tests against SPEC 5.1's tomato shipping-date comparison table."""

import pytest

from app.services.pricing import PricePoint, best_shipping_date, build_shipping_date_options


def _spec_candidates() -> list[PricePoint]:
    return [
        PricePoint("2026-08-08", 2450),
        PricePoint("2026-08-10", 2580),
        PricePoint("2026-08-17", 2320),
    ]


class TestBuildShippingDateOptions:
    def test_expected_revenue_matches_spec(self):
        results = {r.date: r for r in build_shipping_date_options(1000, 2450, _spec_candidates())}
        assert results["2026-08-08"].expected_revenue == 2_450_000
        assert results["2026-08-10"].expected_revenue == 2_580_000
        assert results["2026-08-17"].expected_revenue == 2_320_000

    def test_price_change_percent_matches_spec(self):
        results = {r.date: r for r in build_shipping_date_options(1000, 2450, _spec_candidates())}
        assert results["2026-08-08"].price_change_percent == 0.0
        assert results["2026-08-10"].price_change_percent == pytest.approx(5.3, abs=0.05)
        assert results["2026-08-17"].price_change_percent == pytest.approx(-5.3, abs=0.05)

    def test_supply_condition_labels(self):
        results = {r.date: r for r in build_shipping_date_options(1000, 2450, _spec_candidates())}
        assert results["2026-08-08"].market_supply_condition == "공급량 보통"
        assert results["2026-08-10"].market_supply_condition == "공급량 감소 예상"
        assert results["2026-08-17"].market_supply_condition == "공급량 증가 예상"

    def test_best_shipping_date_is_highest_revenue(self):
        results = build_shipping_date_options(1000, 2450, _spec_candidates())
        assert best_shipping_date(results).date == "2026-08-10"

    def test_rejects_non_positive_quantity(self):
        with pytest.raises(ValueError):
            build_shipping_date_options(0, 2450, _spec_candidates())
