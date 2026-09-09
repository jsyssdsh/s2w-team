"""Tests for /api/farmlands routes."""


class TestListFarmlands:
    async def test_idle_status_filter_excludes_operating_land(self, client):
        resp = await client.get("/api/farmlands?status=idle")
        assert resp.status_code == 200
        ids = {f["id"] for f in resp.json()}
        assert ids == {"farmland-a", "farmland-b", "farmland-c"}

    async def test_response_includes_coordinates_for_map_pins(self, client):
        """Nullable since db/seed.sql doesn't set real coordinates yet, but the
        field must be present so the frontend map can read it once it is."""
        resp = await client.get("/api/farmlands?status=idle")
        assert resp.status_code == 200
        for farmland in resp.json():
            assert "latitude" in farmland
            assert "longitude" in farmland


class TestFarmlandDetail:
    async def test_detail_includes_operating_smart_farm_and_latest_sensors(self, client):
        resp = await client.get("/api/farmlands/farmland-existing")
        assert resp.status_code == 200
        body = resp.json()
        assert body["smart_farm"]["id"] == "smart-farm-tomato"
        readings = body["smart_farm"]["latest_sensor_readings"]
        assert readings["temperature"] == 26.5  # latest of before/after per SPEC 5.5
        assert readings["soil_moisture"] == 41

    async def test_detail_has_no_smart_farm_for_idle_land(self, client):
        resp = await client.get("/api/farmlands/farmland-a")
        assert resp.status_code == 200
        assert resp.json()["smart_farm"] is None

    async def test_404_for_unknown_farmland(self, client):
        resp = await client.get("/api/farmlands/nope")
        assert resp.status_code == 404


class TestFarmlandRecommendation:
    async def test_matches_spec_5_6_ranking(self, client):
        resp = await client.post(
            "/api/farmlands/recommendation",
            json={
                "user_id": "user-farmer-lee",
                "desired_crop": "딸기",
                "desired_area_pyeong": 850,
                "budget_monthly_rent_krw": 700000,
            },
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["recommended_farmland_id"] == "farmland-a"
        ranks = {o["farmland_id"]: o["rank"] for o in body["options"]}
        assert ranks["farmland-a"] == 1
        assert ranks["farmland-b"] == 2
        assert ranks["farmland-c"] == 3
