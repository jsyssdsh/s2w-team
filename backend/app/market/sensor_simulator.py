"""Live smart-farm sensor simulator, driving the /api/stream/sensors SSE feed.

This only produces the visual "live" wiggle for dashboards when there is no
real ESP32 hardware attached (SPEC 6.1: 스마트팜 IoT 센서 -> MQTT -> 서버). It does
not persist to sensor_readings -- that table is written by the explicit
ingest endpoint (app.routes.sensors), matching the real architecture where
the ESP32, not this simulator, is the source of truth for recorded history.
It also does not evaluate against a crop's optimal range; see
app.services.sensors for that (kept separate so simulation and evaluation
can be tested/reasoned about independently).

A stream code is "{smart_farm_id}:{metric}".
"""

from __future__ import annotations

import asyncio
import logging
import random

from .cache import PriceCache

logger = logging.getLogger(__name__)

# Generic starting point per metric when a farm has no recorded reading yet.
DEFAULT_BASELINE_BY_METRIC: dict[str, float] = {
    "temperature": 25.0,
    "humidity": 65.0,
    "soil_moisture": 45.0,
    "light": 19000.0,
}

# Absolute (not relative) per-tick noise scale -- sensor values can sit near
# zero (e.g. soil moisture), where relative noise would misbehave.
NOISE_SCALE_BY_METRIC: dict[str, float] = {
    "temperature": 0.15,
    "humidity": 0.5,
    "soil_moisture": 0.6,
    "light": 150.0,
}
DEFAULT_NOISE_SCALE = 0.5
REVERSION_RATE = 0.05

SENSOR_METRICS: tuple[str, ...] = ("temperature", "humidity", "soil_moisture", "light")


def make_code(smart_farm_id: str, metric: str) -> str:
    return f"{smart_farm_id}:{metric}"


def metric_of(code: str) -> str:
    return code.rsplit(":", 1)[-1]


class SensorSimulator:
    """Mean-reverting random walk per (smart_farm_id, metric) series."""

    def __init__(self, initial_values: dict[str, float]) -> None:
        self._baselines: dict[str, float] = dict(initial_values)
        self._values: dict[str, float] = dict(initial_values)

    def step(self) -> dict[str, float]:
        result: dict[str, float] = {}
        for code, value in self._values.items():
            metric = metric_of(code)
            baseline = self._baselines[code]
            noise_scale = NOISE_SCALE_BY_METRIC.get(metric, DEFAULT_NOISE_SCALE)

            reversion = REVERSION_RATE * (baseline - value)
            noise = random.gauss(0, noise_scale)
            new_value = max(value + reversion + noise, 0.0)

            self._values[code] = new_value
            result[code] = round(new_value, 1)
        return result

    def add_series(self, smart_farm_id: str, metric: str, initial_value: float | None = None) -> None:
        code = make_code(smart_farm_id, metric)
        if code in self._values:
            return
        value = initial_value if initial_value is not None else DEFAULT_BASELINE_BY_METRIC.get(metric, 0.0)
        self._baselines[code] = value
        self._values[code] = value

    def remove_series(self, smart_farm_id: str, metric: str) -> None:
        code = make_code(smart_farm_id, metric)
        self._values.pop(code, None)
        self._baselines.pop(code, None)

    def get_value(self, smart_farm_id: str, metric: str) -> float | None:
        return self._values.get(make_code(smart_farm_id, metric))

    def get_codes(self) -> list[str]:
        return list(self._values.keys())


class SensorStream:
    """Background asyncio task that steps a SensorSimulator into a PriceCache."""

    def __init__(self, price_cache: PriceCache, update_interval: float = 2.0) -> None:
        self._cache = price_cache
        self._interval = update_interval
        self._sim: SensorSimulator | None = None
        self._task: asyncio.Task | None = None

    async def start(self, initial_values: dict[str, float]) -> None:
        """initial_values: {"{smart_farm_id}:{metric}": value}, e.g. seeded from
        app.db.get_latest_sensor_readings for every active smart farm."""
        self._sim = SensorSimulator(initial_values)
        for code, value in initial_values.items():
            self._cache.update(code=code, price=value)
        self._task = asyncio.create_task(self._run_loop(), name="sensor-stream")
        logger.info("Sensor stream started with %d series", len(initial_values))

    async def stop(self) -> None:
        if self._task and not self._task.done():
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        self._task = None
        logger.info("Sensor stream stopped")

    async def _run_loop(self) -> None:
        while True:
            try:
                if self._sim:
                    values = self._sim.step()
                    for code, value in values.items():
                        self._cache.update(code=code, price=value)
            except Exception:
                logger.exception("Sensor simulator step failed")
            await asyncio.sleep(self._interval)
