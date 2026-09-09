"""Tests for SensorSimulator / SensorStream."""

import asyncio

import pytest

from app.market.cache import PriceCache
from app.market.sensor_simulator import (
    DEFAULT_BASELINE_BY_METRIC,
    SensorSimulator,
    SensorStream,
    make_code,
    metric_of,
)


class TestCodeHelpers:
    def test_make_code(self):
        assert make_code("smart-farm-1", "temperature") == "smart-farm-1:temperature"

    def test_metric_of(self):
        assert metric_of("smart-farm-1:temperature") == "temperature"


class TestSensorSimulator:
    def test_step_returns_all_series(self):
        sim = SensorSimulator({"farm-1:temperature": 25.0, "farm-1:humidity": 65.0})
        result = sim.step()
        assert set(result.keys()) == {"farm-1:temperature", "farm-1:humidity"}

    def test_values_never_negative(self):
        sim = SensorSimulator({"farm-1:soil_moisture": 1.0})
        for _ in range(2000):
            values = sim.step()
            assert values["farm-1:soil_moisture"] >= 0

    def test_add_series_uses_default_baseline(self):
        sim = SensorSimulator({})
        sim.add_series("farm-1", "temperature")
        assert sim.get_value("farm-1", "temperature") == DEFAULT_BASELINE_BY_METRIC["temperature"]

    def test_add_series_uses_given_initial_value(self):
        sim = SensorSimulator({})
        sim.add_series("farm-1", "temperature", initial_value=29.4)
        assert sim.get_value("farm-1", "temperature") == 29.4

    def test_add_duplicate_is_noop(self):
        sim = SensorSimulator({})
        sim.add_series("farm-1", "temperature", initial_value=29.4)
        sim.add_series("farm-1", "temperature", initial_value=10.0)
        assert sim.get_value("farm-1", "temperature") == 29.4

    def test_remove_series(self):
        sim = SensorSimulator({"farm-1:temperature": 25.0})
        sim.remove_series("farm-1", "temperature")
        assert sim.get_value("farm-1", "temperature") is None

    def test_value_stays_near_baseline_over_many_steps(self):
        sim = SensorSimulator({"farm-1:temperature": 25.0})
        for _ in range(500):
            sim.step()
        assert abs(sim.get_value("farm-1", "temperature") - 25.0) < 10


@pytest.mark.asyncio
class TestSensorStream:
    async def test_start_populates_cache(self):
        cache = PriceCache()
        stream = SensorStream(cache, update_interval=0.1)
        await stream.start({"farm-1:temperature": 25.0, "farm-1:humidity": 65.0})

        assert cache.get("farm-1:temperature") is not None
        assert cache.get("farm-1:humidity") is not None

        await stream.stop()

    async def test_values_update_over_time(self):
        cache = PriceCache()
        stream = SensorStream(cache, update_interval=0.05)
        await stream.start({"farm-1:temperature": 25.0})

        initial_version = cache.version
        await asyncio.sleep(0.3)

        assert cache.version > initial_version

        await stream.stop()

    async def test_stop_is_idempotent(self):
        cache = PriceCache()
        stream = SensorStream(cache, update_interval=0.1)
        await stream.start({"farm-1:temperature": 25.0})
        await stream.stop()
        await stream.stop()  # Should not raise
