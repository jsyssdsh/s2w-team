"""Tests for /api/wholesaler routes."""


class TestWholesalerDashboard:
    async def test_dashboard_recommends_matching_farmer_shipments(self, client):
        resp = await client.get("/api/wholesaler/wholesaler-b/dashboard")
        assert resp.status_code == 200
        body = resp.json()
        assert body["wholesaler_name"] == "도매처 B"
        shipment_ids = {s["shipment_plan_id"] for s in body["recommended_farmer_shipments"]}
        assert "shipment-tomato-main" in shipment_ids
        matched = next(
            s for s in body["recommended_farmer_shipments"] if s["shipment_plan_id"] == "shipment-tomato-main"
        )
        assert matched["recommended_trade_price_krw_per_kg"] == 2580

    async def test_dashboard_404_for_unknown_wholesaler(self, client):
        resp = await client.get("/api/wholesaler/nope/dashboard")
        assert resp.status_code == 404


class TestBuyerRecommendation:
    async def test_matches_spec_5_3_grade_mapping(self, client):
        resp = await client.post(
            "/api/wholesaler/buyer-recommendation",
            json={
                "shipment_plan_ids": [
                    "shipment-tomato-premium",
                    "shipment-tomato-standard",
                    "shipment-tomato-offgrade",
                    "shipment-tomato-urgent",
                ]
            },
        )
        assert resp.status_code == 200
        by_id = {m["shipment_plan_id"]: m for m in resp.json()["matches"]}
        assert by_id["shipment-tomato-premium"]["recommended_retailer_type"] == "대형마트"
        assert by_id["shipment-tomato-premium"]["matched_retailer_name"] == "한마음 대형마트"
        assert by_id["shipment-tomato-standard"]["recommended_retailer_type"] == "학교급식"
        assert by_id["shipment-tomato-offgrade"]["recommended_retailer_type"] == "가공업체"
        assert by_id["shipment-tomato-urgent"]["recommended_retailer_type"] == "지역음식점"

    async def test_404_for_unknown_shipment_plan(self, client):
        resp = await client.post("/api/wholesaler/buyer-recommendation", json={"shipment_plan_ids": ["nope"]})
        assert resp.status_code == 404
