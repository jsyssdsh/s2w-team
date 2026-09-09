"""FastAPI application for S2W (울퉁불퉁 농장 AI)."""

import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.db import get_latest_sensor_readings, init_db, list_crops, list_smart_farms, seed_demo_data
from app.market import CropPriceStream, PriceCache, SensorStream, create_stream_router, make_code
from app.market.sensor_simulator import SENSOR_METRICS
from app.routes import (
    chat,
    crops,
    farmer,
    farmland,
    sensors,
    supply_risk,
    transactions,
    wholesaler,
)

logger = logging.getLogger(__name__)

# Module-level caches -- shared between their SSE router and the lifespan
# background streams. Two separate caches (not one) so a crop name and a
# smart-farm sensor code can never collide.
price_cache = PriceCache()
sensor_cache = PriceCache()


async def _collect_initial_sensor_values() -> dict[str, float]:
    """Seed the live sensor stream from each active smart farm's last
    recorded reading, falling back to the simulator's per-metric defaults
    for metrics that have never been recorded."""
    values: dict[str, float] = {}
    for farm in await list_smart_farms():
        readings = await get_latest_sensor_readings(farm["id"])
        for metric in SENSOR_METRICS:
            if metric in readings:
                values[make_code(farm["id"], metric)] = readings[metric]["value"]
    return values


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup/shutdown lifecycle."""
    await init_db()

    # First boot against an empty volume (e.g. a fresh container) has no demo
    # data yet -- seed it once so the prototype is usable immediately without
    # a manual step. crops is the narrowest existence check available (every
    # other seeded table references a crop), and re-running init_db() never
    # touches it, so this only fires on a genuinely empty database.
    if not await list_crops():
        await seed_demo_data()
        logger.info("Database was empty -- loaded demo dataset from db/seed.sql")

    app.state.price_cache = price_cache
    app.state.sensor_cache = sensor_cache

    crop_names = [c["name"] for c in await list_crops()]
    crop_stream = CropPriceStream(price_cache)
    await crop_stream.start(crop_names)

    sensor_stream = SensorStream(sensor_cache)
    await sensor_stream.start(await _collect_initial_sensor_values())

    logger.info("Live streams started: %d crops, %d sensor series", len(crop_names), len(sensor_cache))

    yield

    await crop_stream.stop()
    await sensor_stream.stop()
    logger.info("Live streams stopped")


app = FastAPI(title="S2W - 울퉁불퉁 농장 AI", lifespan=lifespan)

# API routes
app.include_router(crops.router)
app.include_router(farmer.router)
app.include_router(wholesaler.router)
app.include_router(farmland.router)
app.include_router(sensors.router)
app.include_router(supply_risk.router)
app.include_router(transactions.router)
app.include_router(chat.router)

# SSE streaming -- separate feeds for crop prices and smart-farm sensors
app.include_router(create_stream_router(price_cache, path="/prices", tag="crop-prices"))
app.include_router(create_stream_router(sensor_cache, path="/sensors", tag="sensors"))


@app.get("/api/health")
async def health():
    return {"status": "ok"}


# Static files serving (frontend) -- mount last so API routes take priority
_static_dir = Path(__file__).parent.parent / "static"
if _static_dir.is_dir():
    app.mount("/", StaticFiles(directory=str(_static_dir), html=True), name="static")
