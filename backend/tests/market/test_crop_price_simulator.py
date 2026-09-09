"""Tests for CropPriceSimulator / CropPriceStream."""

import asyncio

import pytest

from app.market.cache import PriceCache
from app.market.crop_price_simulator import CropPriceSimulator, CropPriceStream
from app.market.seed_data import SEED_CROP_PRICES


class TestCropPriceSimulator:
    def test_step_returns_all_crops(self):
        sim = CropPriceSimulator(["토마토", "양파"])
        result = sim.step()
        assert set(result.keys()) == {"토마토", "양파"}

    def test_prices_are_positive(self):
        sim = CropPriceSimulator(["토마토"])
        for _ in range(2000):
            prices = sim.step()
            assert prices["토마토"] > 0

    def test_initial_price_matches_seed(self):
        sim = CropPriceSimulator(["토마토"])
        assert sim.get_price("토마토") == SEED_CROP_PRICES["토마토"]

    def test_unknown_crop_gets_default_seed(self):
        sim = CropPriceSimulator(["새작물"])
        assert sim.get_price("새작물") == 1000.0

    def test_add_crop(self):
        sim = CropPriceSimulator(["토마토"])
        sim.add_crop("딸기")
        result = sim.step()
        assert "딸기" in result

    def test_add_duplicate_is_noop(self):
        sim = CropPriceSimulator(["토마토"])
        sim.add_crop("토마토")
        assert sim.get_crops() == ["토마토"]

    def test_remove_crop(self):
        sim = CropPriceSimulator(["토마토", "양파"])
        sim.remove_crop("양파")
        result = sim.step()
        assert "양파" not in result
        assert "토마토" in result

    def test_remove_nonexistent_is_noop(self):
        sim = CropPriceSimulator(["토마토"])
        sim.remove_crop("없음")  # Should not raise

    def test_empty_step(self):
        sim = CropPriceSimulator([])
        assert sim.step() == {}

    def test_price_stays_near_baseline_over_many_steps(self):
        """Mean reversion should keep the price from drifting away permanently."""
        sim = CropPriceSimulator(["토마토"])
        baseline = SEED_CROP_PRICES["토마토"]
        for _ in range(500):
            sim.step()
        final_price = sim.get_price("토마토")
        assert abs(final_price - baseline) / baseline < 0.5


@pytest.mark.asyncio
class TestCropPriceStream:
    async def test_start_populates_cache(self):
        cache = PriceCache()
        stream = CropPriceStream(cache, update_interval=0.1)
        await stream.start(["토마토", "양파"])

        assert cache.get("토마토") is not None
        assert cache.get("양파") is not None

        await stream.stop()

    async def test_prices_update_over_time(self):
        cache = PriceCache()
        stream = CropPriceStream(cache, update_interval=0.05)
        await stream.start(["토마토"])

        initial_version = cache.version
        await asyncio.sleep(0.3)

        assert cache.version > initial_version

        await stream.stop()

    async def test_stop_is_idempotent(self):
        cache = PriceCache()
        stream = CropPriceStream(cache, update_interval=0.1)
        await stream.start(["토마토"])
        await stream.stop()
        await stream.stop()  # Should not raise
