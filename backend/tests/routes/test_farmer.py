"""Tests for /api/farmer routes, against the SPEC demo dataset (db/seed.sql)."""


class TestShipmentPlans:
    async def test_list_shipment_plans(self, client):
        resp = await client.get("/api/farmer/user-farmer-kim/shipment-plans?status=planned")
        assert resp.status_code == 200
        ids = {p["id"] for p in resp.json()}
        assert "shipment-tomato-main" in ids
        plan = next(p for p in resp.json() if p["id"] == "shipment-tomato-main")
        assert plan["crop_name"] == "토마토"

    async def test_create_shipment_plan(self, client):
        resp = await client.post(
            "/api/farmer/shipment-plans",
            json={
                "farmer_user_id": "user-farmer-kim",
                "crop_id": "crop-strawberry",
                "expected_yield_kg": 500,
                "planned_shipment_date": "2026-10-01",
                "grade": "상품",
            },
        )
        assert resp.status_code == 201
        body = resp.json()
        assert body["crop_name"] == "딸기"
        assert body["status"] == "planned"


class TestFarmerDashboard:
    async def test_dashboard_returns_farmer_and_smart_farms(self, client):
        resp = await client.get("/api/farmer/user-farmer-kim/dashboard")
        assert resp.status_code == 200
        body = resp.json()
        assert body["farmer_name"] == "김농부"
        farm_ids = {f["id"] for f in body["smart_farms"]}
        assert "smart-farm-tomato" in farm_ids

    async def test_dashboard_404_for_unknown_farmer(self, client):
        resp = await client.get("/api/farmer/nope/dashboard")
        assert resp.status_code == 404


class TestPriceForecast:
    async def test_matches_spec_5_1_numbers(self, client):
        """SPEC 5.1's tomato 3-date comparison, using db/seed.sql's exact prices."""
        resp = await client.post(
            "/api/farmer/price-forecast",
            json={
                "shipment_plan_id": "shipment-tomato-main",
                "candidate_dates": ["2026-08-08", "2026-08-10", "2026-08-17"],
            },
        )
        assert resp.status_code == 200
        options = {o["date"]: o for o in resp.json()["options"]}
        assert options["2026-08-08"]["expected_revenue"] == 2_450_000
        assert options["2026-08-10"]["expected_revenue"] == 2_580_000
        assert options["2026-08-17"]["expected_revenue"] == 2_320_000
        assert resp.json()["recommended_date"] == "2026-08-10"

    async def test_404_for_unknown_shipment_plan(self, client):
        resp = await client.post("/api/farmer/price-forecast", json={"shipment_plan_id": "nope"})
        assert resp.status_code == 404


class TestWholesalerRecommendation:
    async def test_matches_spec_5_2_ranking(self, client):
        resp = await client.post(
            "/api/farmer/wholesaler-recommendation", json={"shipment_plan_id": "shipment-tomato-main"}
        )
        assert resp.status_code == 200
        body = resp.json()
        by_name = {o["wholesaler_name"]: o for o in body["options"]}
        assert by_name["도매처 B"]["rank"] == 1
        assert by_name["도매처 A"]["rank"] == 2
        assert by_name["도매처 C"]["rank"] == 3
        assert by_name["도매처 B"]["net_profit_krw"] == 2_422_600
        assert body["recommended_wholesaler"] == "도매처 B"
