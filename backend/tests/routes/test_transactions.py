"""Tests for /api/transactions."""


class TestCreateTransaction:
    async def test_net_profit_matches_spec_5_2_formula(self, client):
        resp = await client.post(
            "/api/transactions",
            json={
                "shipment_plan_id": "shipment-tomato-main",
                "counterparty_type": "wholesaler",
                "wholesaler_id": "wholesaler-b",
                "quantity_kg": 1000,
                "unit_price_krw_per_kg": 2580,
                "transport_cost_krw": 80000,
                "commission_rate": 0.03,
            },
        )
        assert resp.status_code == 201
        body = resp.json()
        assert body["net_profit_krw"] == 2_422_600
        assert body["status"] == "requested"

    async def test_missing_counterparty_id_rejected(self, client):
        resp = await client.post(
            "/api/transactions",
            json={
                "shipment_plan_id": "shipment-tomato-main",
                "counterparty_type": "wholesaler",
                "quantity_kg": 1000,
                "unit_price_krw_per_kg": 2580,
            },
        )
        assert resp.status_code == 422

    async def test_404_for_unknown_shipment_plan(self, client):
        resp = await client.post(
            "/api/transactions",
            json={
                "shipment_plan_id": "nope",
                "counterparty_type": "wholesaler",
                "wholesaler_id": "wholesaler-b",
                "quantity_kg": 100,
                "unit_price_krw_per_kg": 2000,
            },
        )
        assert resp.status_code == 404


class TestListAndUpdateTransactions:
    async def test_list_includes_seeded_transaction(self, client):
        resp = await client.get("/api/transactions", params={"shipment_plan_id": "shipment-tomato-main"})
        assert resp.status_code == 200
        ids = {t["id"] for t in resp.json()}
        assert "txn-tomato-main" in ids

    async def test_update_status(self, client):
        resp = await client.patch("/api/transactions/txn-tomato-main/status", json={"status": "cancelled"})
        assert resp.status_code == 200
        assert resp.json()["status"] == "cancelled"

    async def test_invalid_status_rejected(self, client):
        resp = await client.patch("/api/transactions/txn-tomato-main/status", json={"status": "bogus"})
        assert resp.status_code == 400

    async def test_404_for_unknown_transaction(self, client):
        resp = await client.patch("/api/transactions/nope/status", json={"status": "accepted"})
        assert resp.status_code == 404
