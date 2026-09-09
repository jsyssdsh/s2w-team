"""Tests for /api/crops."""


class TestCrops:
    async def test_list_crops(self, client):
        resp = await client.get("/api/crops")
        assert resp.status_code == 200
        names = {c["name"] for c in resp.json()}
        assert names == {"토마토", "양파", "딸기"}
