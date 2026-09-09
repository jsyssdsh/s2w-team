"""Tests for /api/supply-risk, against SPEC 5.4's onion scenario."""


class TestSupplyRisk:
    async def test_matches_spec_5_4_onion_scenario(self, client):
        resp = await client.post(
            "/api/supply-risk", json={"crop_name": "양파", "region": "충남 논산시"}
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["total_supply_ton"] == 128.0
        assert body["excess_supply_ton"] == 28.0
        assert body["risk_level"] == "위험"
        channels = {p["channel"]: p["processed_volume_ton"] for p in body["response_plan"]}
        assert channels["식품가공업체 추가 연결"] == 12.0

    async def test_404_for_unknown_crop(self, client):
        resp = await client.post("/api/supply-risk", json={"crop_name": "없는작물", "region": "충남 논산시"})
        assert resp.status_code == 404
