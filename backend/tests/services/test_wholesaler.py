"""Tests against SPEC 5.2's tomato wholesaler comparison table."""

from app.services.wholesaler import WholesalerOfferInput, rank_wholesaler_offers


def _spec_offers() -> list[WholesalerOfferInput]:
    return [
        WholesalerOfferInput("wholesaler-a", "A", 2550, 1000, 180000, 0.03),
        WholesalerOfferInput("wholesaler-b", "B", 2580, 1000, 80000, 0.03),
        WholesalerOfferInput("wholesaler-c", "C", 2700, 800, 210000, 0.03),
    ]


class TestRankWholesalerOffers:
    def test_ranks_b_first_a_second_c_third(self):
        """Matches SPEC 5.2's stated order (B=1위, A=2위, C=3위)."""
        results = {r.wholesaler_name: r for r in rank_wholesaler_offers(1000, _spec_offers())}
        assert results["B"].rank == 1
        assert results["A"].rank == 2
        assert results["C"].rank == 3

    def test_wholesaler_b_net_profit_matches_spec_exactly(self):
        results = {r.wholesaler_name: r for r in rank_wholesaler_offers(1000, _spec_offers())}
        assert results["B"].net_profit_krw == 2_422_600

    def test_wholesaler_c_net_profit_matches_spec_exactly(self):
        results = {r.wholesaler_name: r for r in rank_wholesaler_offers(1000, _spec_offers())}
        assert results["C"].net_profit_krw == 1_885_200

    def test_wholesaler_c_capacity_limits_sellable_quantity(self):
        """C can only buy 800kg of the 1,000kg lot -- SPEC 5.2's key example."""
        results = {r.wholesaler_name: r for r in rank_wholesaler_offers(1000, _spec_offers())}
        assert results["C"].sellable_quantity_kg == 800

    def test_rejects_non_positive_quantity(self):
        import pytest

        with pytest.raises(ValueError):
            rank_wholesaler_offers(0, _spec_offers())
