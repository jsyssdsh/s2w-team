"""Verifies db/seed.sql reproduces the numbers in planning/SPEC.md section 5.

Runs seed_demo_data() against a temp database (never a developer's real db
file) and checks the figures a reader would expect from the spec's example
tables, so a future edit to seed.sql that breaks fidelity to the spec fails
loudly here instead of silently in the UI.
"""

import pytest

from app.db import (
    get_price_history,
    get_recommendations_for_subject,
    get_retailer_candidates_for_grade,
    get_supply_demand_balance,
    get_wholesaler_candidates,
    init_db,
    search_farmlands,
    seed_demo_data,
    set_db_path,
)


@pytest.fixture(autouse=True)
async def seeded_db(tmp_path):
    db_path = str(tmp_path / "test.db")
    set_db_path(db_path)
    await init_db()
    await seed_demo_data()
    yield db_path


class TestPriceForecastSeed:
    async def test_tomato_forecast_dates_match_spec_5_1(self):
        history = await get_price_history("crop-tomato", region="충남 논산시")
        by_date = {h["price_date"]: h["wholesale_price_krw_per_kg"] for h in history}
        assert by_date["2026-08-08"] == 2450
        assert by_date["2026-08-10"] == 2580
        assert by_date["2026-08-17"] == 2320

    async def test_price_forecast_recommendations_ranked_best_first(self):
        recs = await get_recommendations_for_subject(
            "shipment_plan", "shipment-tomato-main", recommendation_type="price_forecast"
        )
        assert [r["target_id"] for r in recs] == ["2026-08-10", "2026-08-08", "2026-08-17"]
        assert [r["score"] for r in recs] == [2580000, 2450000, 2320000]


class TestWholesalerComparisonSeed:
    async def test_offers_match_spec_5_2_table(self):
        candidates = await get_wholesaler_candidates("crop-tomato")
        by_name = {c["wholesaler_name"]: c for c in candidates}

        assert by_name["도매처 A"]["purchase_unit_price_krw_per_kg"] == 2550
        assert by_name["도매처 A"]["purchase_capacity_kg"] == 1000
        assert by_name["도매처 A"]["transport_cost_krw"] == 180000

        assert by_name["도매처 B"]["purchase_unit_price_krw_per_kg"] == 2580
        assert by_name["도매처 B"]["transport_cost_krw"] == 80000

        assert by_name["도매처 C"]["purchase_unit_price_krw_per_kg"] == 2700
        assert by_name["도매처 C"]["purchase_capacity_kg"] == 800

    async def test_recommendation_ranking_picks_wholesaler_b(self):
        recs = await get_recommendations_for_subject(
            "shipment_plan", "shipment-tomato-main", recommendation_type="wholesaler_match"
        )
        assert recs[0]["target_id"] == "wholesaler-b"
        assert recs[0]["score"] == 2422600
        assert recs[0]["outcome"] == "selected"


class TestRetailerMatchingSeed:
    async def test_grade_matches_spec_5_3_table(self):
        premium = await get_retailer_candidates_for_grade("crop-tomato", "특상품")
        standard = await get_retailer_candidates_for_grade("crop-tomato", "상품")
        offgrade = await get_retailer_candidates_for_grade("crop-tomato", "규격외")
        urgent = await get_retailer_candidates_for_grade("crop-tomato", "판매기한임박")

        assert premium[0]["retailer_type"] == "대형마트"
        assert premium[0]["demand_quantity_kg"] == 300
        assert standard[0]["retailer_type"] == "학교급식"
        assert standard[0]["demand_quantity_kg"] == 700
        assert offgrade[0]["retailer_type"] == "가공업체"
        assert offgrade[0]["demand_quantity_kg"] == 500
        assert urgent[0]["retailer_type"] == "지역음식점"
        assert urgent[0]["demand_quantity_kg"] == 200


class TestSupplyRiskSeed:
    async def test_onion_balance_matches_spec_5_4_table(self):
        balance = await get_supply_demand_balance("crop-onion", region="충남 논산시")
        assert balance["farmer_planned_kg"] == 120000
        assert balance["wholesaler_inventory_kg"] == 8000
        assert balance["total_supply_kg"] == 128000
        assert balance["retailer_demand_kg"] == 100000
        assert balance["excess_supply_kg"] == 28000

    async def test_supply_risk_recommendation_metadata_has_mitigation_plan(self):
        recs = await get_recommendations_for_subject(
            "crop", "crop-onion", recommendation_type="supply_risk_alert"
        )
        assert len(recs) == 1
        metadata = recs[0]["metadata"]
        assert metadata["excess_supply_kg"] == 28000
        assert metadata["risk_level"] == "위험"
        total_mitigation = sum(m["quantity_kg"] for m in metadata["mitigation_plan"])
        assert total_mitigation == 28000


class TestFarmlandComparisonSeed:
    async def test_farmland_abc_match_spec_5_6_table(self):
        farmlands = {f["id"]: f for f in await search_farmlands(region="충남 논산시", status="idle")}

        assert farmlands["farmland-a"]["area_pyeong"] == 900
        assert farmlands["farmland-a"]["monthly_rent_krw"] == 650000
        assert farmlands["farmland-a"]["has_water_access"] == 1
        assert farmlands["farmland-a"]["has_cold_storage_access"] == 1
        assert farmlands["farmland-a"]["distance_to_wholesaler_km"] == 24

        assert farmlands["farmland-b"]["area_pyeong"] == 1000
        assert farmlands["farmland-b"]["monthly_rent_krw"] == 550000
        assert farmlands["farmland-b"]["has_cold_storage_access"] == 0

        assert farmlands["farmland-c"]["area_pyeong"] == 750
        assert farmlands["farmland-c"]["has_water_access"] == 0

    async def test_farmlands_have_map_coordinates(self):
        """Frontend's farmland map (SPEC 4.4) needs a real lat/long per pin."""
        farmlands = await search_farmlands(region="충남 논산시")
        coords = [(f["id"], f["latitude"], f["longitude"]) for f in farmlands]

        assert len(coords) == 4
        seen_points = set()
        for farmland_id, lat, lng in coords:
            assert lat is not None, f"{farmland_id} missing latitude"
            assert lng is not None, f"{farmland_id} missing longitude"
            # Sanity-bound to roughly the Nonsan/Buyeo area of South Chungnam.
            assert 35.9 <= lat <= 36.4
            assert 126.6 <= lng <= 127.3
            seen_points.add((lat, lng))
        assert len(seen_points) == 4, "each demo farmland should get a distinct point"

    async def test_farmland_recommendation_ranking_matches_spec(self):
        recs = await get_recommendations_for_subject(
            "user", "user-farmer-lee", recommendation_type="farmland_match"
        )
        assert [r["target_id"] for r in recs] == ["farmland-a", "farmland-b", "farmland-c"]
