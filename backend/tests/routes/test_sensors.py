"""Tests for /api/smart-farms/{id}/sensors routes."""


class TestIngestSensorReading:
    async def test_out_of_range_reading_triggers_control_action(self, client):
        resp = await client.post(
            "/api/smart-farms/smart-farm-tomato/sensors",
            params={"crop_id": "crop-tomato"},
            json={"metric": "temperature", "value": 29.4, "unit": "celsius"},
        )
        assert resp.status_code == 201
        body = resp.json()
        assert body["status"] == "기준초과"
        assert body["control_action"] == "환기 작동"

    async def test_without_crop_id_records_but_does_not_evaluate(self, client):
        resp = await client.post(
            "/api/smart-farms/smart-farm-tomato/sensors",
            json={"metric": "soil_moisture", "value": 28, "unit": "percent"},
        )
        assert resp.status_code == 201
        body = resp.json()
        assert body["status"] == "정상"
        assert body["control_action"] is None

    async def test_unknown_metric_rejected(self, client):
        resp = await client.post(
            "/api/smart-farms/smart-farm-tomato/sensors",
            json={"metric": "wind_speed", "value": 5, "unit": "m/s"},
        )
        assert resp.status_code == 400

    async def test_404_for_unknown_farm(self, client):
        resp = await client.post(
            "/api/smart-farms/nope/sensors",
            json={"metric": "temperature", "value": 25, "unit": "celsius"},
        )
        assert resp.status_code == 404


class TestLatestReadings:
    async def test_evaluates_against_crop_optimal_range(self, client):
        resp = await client.get(
            "/api/smart-farms/smart-farm-tomato/sensors/latest", params={"crop_id": "crop-tomato"}
        )
        assert resp.status_code == 200
        by_metric = {r["metric"]: r for r in resp.json()}
        assert by_metric["humidity"]["status"] == "정상"


class TestSensorHistory:
    async def test_returns_readings_in_range(self, client):
        resp = await client.get(
            "/api/smart-farms/smart-farm-tomato/sensors/history",
            params={"metric": "temperature", "start": "2026-08-01T00:00:00+00:00", "end": "2026-08-10T00:00:00+00:00"},
        )
        assert resp.status_code == 200
        values = [r["value"] for r in resp.json()]
        assert values == [29.4, 26.5]
