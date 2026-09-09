"""Thread-safe in-memory cache for live series (crop prices, sensor readings)."""

from __future__ import annotations

import time
from threading import Lock

from .models import PriceUpdate


class PriceCache:
    """Thread-safe in-memory cache of the latest value for each series.

    Writers: CropPriceSimulator or SensorSimulator (one per cache instance).
    Readers: SSE streaming endpoint, and any route that needs the latest value.
    """

    def __init__(self) -> None:
        self._prices: dict[str, PriceUpdate] = {}
        self._lock = Lock()
        self._version: int = 0  # Monotonically increasing; bumped on every update

    def update(self, code: str, price: float, timestamp: float | None = None) -> PriceUpdate:
        """Record a new value for a series. Returns the created PriceUpdate.

        Automatically computes direction and change from the previous value.
        If this is the first update for the series, previous_price == price
        (direction='flat').
        """
        with self._lock:
            ts = timestamp or time.time()
            prev = self._prices.get(code)
            previous_price = prev.price if prev else price

            update = PriceUpdate(
                code=code,
                price=round(price, 2),
                previous_price=round(previous_price, 2),
                timestamp=ts,
            )
            self._prices[code] = update
            self._version += 1
            return update

    def get(self, code: str) -> PriceUpdate | None:
        """Get the latest value for a single series, or None if unknown."""
        with self._lock:
            return self._prices.get(code)

    def get_all(self) -> dict[str, PriceUpdate]:
        """Snapshot of all current values. Returns a shallow copy."""
        with self._lock:
            return dict(self._prices)

    def get_price(self, code: str) -> float | None:
        """Convenience: get just the value float, or None."""
        update = self.get(code)
        return update.price if update else None

    def remove(self, code: str) -> None:
        """Remove a series from the cache (e.g., when it stops being tracked)."""
        with self._lock:
            self._prices.pop(code, None)

    @property
    def version(self) -> int:
        """Current version counter. Useful for SSE change detection."""
        return self._version

    def __len__(self) -> int:
        with self._lock:
            return len(self._prices)

    def __contains__(self, code: str) -> bool:
        with self._lock:
            return code in self._prices
