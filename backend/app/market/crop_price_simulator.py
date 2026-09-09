"""Live crop wholesale-price simulator, driving the /api/stream/prices SSE feed.

Real-time per-second wholesale price ticks don't exist for produce (aT
auctions settle daily), so this is explicitly a demo visualization layer --
a mean-reverting random walk around each crop's latest known market price,
not a forecast. Actual forecasting numbers come from app.services.pricing
against recorded market_prices history, never from this simulator.
"""

from __future__ import annotations

import asyncio
import logging
import random

from .cache import PriceCache
from .seed_data import CROP_SIGMA, DEFAULT_SIGMA, REVERSION_RATE, SEED_CROP_PRICES

logger = logging.getLogger(__name__)


class CropPriceSimulator:
    """Mean-reverting random walk over each crop's wholesale price.

    Unlike the old stock GBM simulator, there is no cross-crop correlation
    model -- produce prices for unrelated crops have no meaningful
    correlation structure worth simulating for a prototype.
    """

    def __init__(self, crop_names: list[str]) -> None:
        self._baselines: dict[str, float] = {}
        self._prices: dict[str, float] = {}
        for name in crop_names:
            self._add_internal(name)

    def step(self) -> dict[str, float]:
        """Advance all tracked crops by one tick. Returns {crop_name: new_price}."""
        result: dict[str, float] = {}
        for name, price in self._prices.items():
            baseline = self._baselines[name]
            sigma = CROP_SIGMA.get(name, DEFAULT_SIGMA)

            reversion = REVERSION_RATE * (baseline - price)
            noise = random.gauss(0, sigma * price)
            new_price = max(price + reversion + noise, 1.0)

            self._prices[name] = new_price
            result[name] = round(new_price, 1)
        return result

    def add_crop(self, name: str) -> None:
        if name in self._prices:
            return
        self._add_internal(name)

    def remove_crop(self, name: str) -> None:
        self._prices.pop(name, None)
        self._baselines.pop(name, None)

    def get_price(self, name: str) -> float | None:
        return self._prices.get(name)

    def get_crops(self) -> list[str]:
        return list(self._prices.keys())

    def _add_internal(self, name: str) -> None:
        seed = SEED_CROP_PRICES.get(name, 1000.0)
        self._baselines[name] = seed
        self._prices[name] = seed


class CropPriceStream:
    """Background asyncio task that steps a CropPriceSimulator into a PriceCache."""

    def __init__(self, price_cache: PriceCache, update_interval: float = 1.0) -> None:
        self._cache = price_cache
        self._interval = update_interval
        self._sim: CropPriceSimulator | None = None
        self._task: asyncio.Task | None = None

    async def start(self, crop_names: list[str]) -> None:
        self._sim = CropPriceSimulator(crop_names)
        for name in crop_names:
            price = self._sim.get_price(name)
            if price is not None:
                self._cache.update(code=name, price=price)
        self._task = asyncio.create_task(self._run_loop(), name="crop-price-stream")
        logger.info("Crop price stream started with %d crops", len(crop_names))

    async def stop(self) -> None:
        if self._task and not self._task.done():
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        self._task = None
        logger.info("Crop price stream stopped")

    async def _run_loop(self) -> None:
        while True:
            try:
                if self._sim:
                    prices = self._sim.step()
                    for name, price in prices.items():
                        self._cache.update(code=name, price=price)
            except Exception:
                logger.exception("Crop price simulator step failed")
            await asyncio.sleep(self._interval)
