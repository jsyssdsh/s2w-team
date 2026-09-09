"""Tests for PriceCache."""

from concurrent.futures import ThreadPoolExecutor

from app.market.cache import PriceCache


class TestPriceCache:
    """Unit tests for the PriceCache."""

    def test_update_and_get(self):
        cache = PriceCache()
        update = cache.update("토마토", 2450.0)
        assert update.code == "토마토"
        assert update.price == 2450.0
        assert cache.get("토마토") == update

    def test_first_update_is_flat(self):
        cache = PriceCache()
        update = cache.update("토마토", 2450.0)
        assert update.direction == "flat"
        assert update.previous_price == 2450.0

    def test_direction_up(self):
        cache = PriceCache()
        cache.update("토마토", 2400.0)
        update = cache.update("토마토", 2450.0)
        assert update.direction == "up"
        assert update.change == 50.0

    def test_direction_down(self):
        cache = PriceCache()
        cache.update("토마토", 2450.0)
        update = cache.update("토마토", 2400.0)
        assert update.direction == "down"
        assert update.change == -50.0

    def test_remove(self):
        cache = PriceCache()
        cache.update("토마토", 2450.0)
        cache.remove("토마토")
        assert cache.get("토마토") is None

    def test_remove_nonexistent(self):
        cache = PriceCache()
        cache.remove("토마토")  # Should not raise

    def test_get_all(self):
        cache = PriceCache()
        cache.update("토마토", 2450.0)
        cache.update("양파", 950.0)
        all_prices = cache.get_all()
        assert set(all_prices.keys()) == {"토마토", "양파"}

    def test_version_increments(self):
        cache = PriceCache()
        v0 = cache.version
        cache.update("토마토", 2450.0)
        assert cache.version == v0 + 1
        cache.update("토마토", 2460.0)
        assert cache.version == v0 + 2

    def test_get_price_convenience(self):
        cache = PriceCache()
        cache.update("토마토", 2450.5)
        assert cache.get_price("토마토") == 2450.5
        assert cache.get_price("없음") is None

    def test_len(self):
        cache = PriceCache()
        assert len(cache) == 0
        cache.update("토마토", 2450.0)
        assert len(cache) == 1
        cache.update("양파", 950.0)
        assert len(cache) == 2

    def test_contains(self):
        cache = PriceCache()
        cache.update("토마토", 2450.0)
        assert "토마토" in cache
        assert "양파" not in cache

    def test_custom_timestamp(self):
        cache = PriceCache()
        custom_ts = 1234567890.0
        update = cache.update("토마토", 2450.5, timestamp=custom_ts)
        assert update.timestamp == custom_ts

    def test_price_rounding(self):
        cache = PriceCache()
        update = cache.update("토마토", 2450.12345)
        assert update.price == 2450.12

    def test_concurrent_updates_single_code_thread_safe(self):
        """Many threads updating the same series should not lose or corrupt updates."""
        cache = PriceCache()
        n_threads = 16
        updates_per_thread = 50

        def worker(_: int) -> None:
            for i in range(updates_per_thread):
                cache.update("토마토", 100.0 + i)

        with ThreadPoolExecutor(max_workers=n_threads) as pool:
            list(pool.map(worker, range(n_threads)))

        # Every update() call increments the version exactly once, even
        # under concurrent access -- a broken lock would lose increments.
        assert cache.version == n_threads * updates_per_thread
        final = cache.get("토마토")
        assert final is not None
        assert 100.0 <= final.price <= 100.0 + updates_per_thread - 1

    def test_concurrent_updates_multiple_codes_thread_safe(self):
        """Concurrent writers across different series must not corrupt the dict."""
        cache = PriceCache()
        codes = [f"crop-{i}" for i in range(20)]

        def worker(code: str) -> None:
            for i in range(25):
                cache.update(code, 50.0 + i)

        with ThreadPoolExecutor(max_workers=len(codes)) as pool:
            list(pool.map(worker, codes))

        assert set(cache.get_all().keys()) == set(codes)
        assert cache.version == len(codes) * 25
