"""Fixtures for route tests."""

import pytest
from httpx import ASGITransport, AsyncClient

from app.db import init_db, seed_demo_data, set_db_path


@pytest.fixture
async def test_db(tmp_path):
    """Create a temporary test database, seeded with the SPEC demo dataset."""
    db_path = str(tmp_path / "test.db")
    set_db_path(db_path)
    await init_db()
    await seed_demo_data()
    yield db_path
    set_db_path(str(tmp_path / "unused.db"))


@pytest.fixture
async def client(test_db, monkeypatch):
    """Async HTTP client wired to the FastAPI app, bypassing lifespan.

    LLM_MOCK=true routes every app.llm call through the deterministic
    template functions in app.llm.mock instead of a real network call.
    """
    monkeypatch.setenv("LLM_MOCK", "true")

    from fastapi import FastAPI

    from app.routes.chat import router as chat_router
    from app.routes.crops import router as crops_router
    from app.routes.farmer import router as farmer_router
    from app.routes.farmland import router as farmland_router
    from app.routes.sensors import router as sensors_router
    from app.routes.supply_risk import router as supply_risk_router
    from app.routes.transactions import router as transactions_router
    from app.routes.wholesaler import router as wholesaler_router

    test_app = FastAPI()
    test_app.include_router(crops_router)
    test_app.include_router(farmer_router)
    test_app.include_router(wholesaler_router)
    test_app.include_router(farmland_router)
    test_app.include_router(sensors_router)
    test_app.include_router(supply_risk_router)
    test_app.include_router(transactions_router)
    test_app.include_router(chat_router)

    @test_app.get("/api/health")
    async def health():
        return {"status": "ok"}

    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
