"""Tests against SPEC 5.6's strawberry farmland A/B/C comparison table."""

from app.services.farmland import FarmlandCandidate, rank_farmland_candidates


def _spec_candidates() -> list[FarmlandCandidate]:
    return [
        FarmlandCandidate("farmland-a", "A", 900, 650_000, True, "가능", 24),
        FarmlandCandidate("farmland-b", "B", 1000, 550_000, True, "제한적", 38),
        FarmlandCandidate("farmland-c", "C", 750, 700_000, False, "가능", 17),
    ]


class TestRankFarmlandCandidates:
    def test_ranks_match_spec_order(self):
        """SPEC 5.6: A=1위, B=2위, C=3위 (C loses despite shortest distance -- no water)."""
        results = {r.name: r for r in rank_farmland_candidates(850, 700_000, _spec_candidates())}
        assert results["A"].rank == 1
        assert results["B"].rank == 2
        assert results["C"].rank == 3

    def test_scores_are_descending_with_rank(self):
        results = rank_farmland_candidates(850, 700_000, _spec_candidates())
        scores = [r.suitability_score for r in results]
        assert scores == sorted(scores, reverse=True)

    def test_no_water_access_is_heavily_penalized(self):
        with_water = FarmlandCandidate("f1", "with-water", 900, 650_000, True, "가능", 24)
        without_water = FarmlandCandidate("f2", "without-water", 900, 650_000, False, "가능", 24)
        results = {
            r.name: r for r in rank_farmland_candidates(900, 650_000, [with_water, without_water])
        }
        assert results["with-water"].suitability_score > results["without-water"].suitability_score
