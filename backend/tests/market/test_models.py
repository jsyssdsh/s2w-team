"""Tests for PriceUpdate dataclass."""

import pytest

from app.market.models import PriceUpdate


class TestPriceUpdate:
    """Unit tests for the PriceUpdate model."""

    def test_price_update_creation(self):
        update = PriceUpdate(code="토마토", price=2450.0, previous_price=2400.0, timestamp=1234567890.0)
        assert update.code == "토마토"
        assert update.price == 2450.0
        assert update.previous_price == 2400.0
        assert update.timestamp == 1234567890.0

    def test_change_calculation(self):
        update = PriceUpdate(code="토마토", price=2450.0, previous_price=2400.0, timestamp=1234567890.0)
        assert update.change == 50.0

    def test_change_negative(self):
        update = PriceUpdate(code="토마토", price=2350.0, previous_price=2400.0, timestamp=1234567890.0)
        assert update.change == -50.0

    def test_change_percent_up(self):
        update = PriceUpdate(code="토마토", price=190.00, previous_price=100.00, timestamp=1234567890.0)
        assert update.change_percent == 90.0

    def test_change_percent_down(self):
        update = PriceUpdate(code="토마토", price=100.00, previous_price=200.00, timestamp=1234567890.0)
        assert update.change_percent == -50.0

    def test_change_percent_zero_previous(self):
        update = PriceUpdate(code="토마토", price=100.00, previous_price=0.00, timestamp=1234567890.0)
        assert update.change_percent == 0.0

    def test_direction_up(self):
        update = PriceUpdate(code="토마토", price=2451.0, previous_price=2450.0, timestamp=1234567890.0)
        assert update.direction == "up"

    def test_direction_down(self):
        update = PriceUpdate(code="토마토", price=2449.0, previous_price=2450.0, timestamp=1234567890.0)
        assert update.direction == "down"

    def test_direction_flat(self):
        update = PriceUpdate(code="토마토", price=2450.0, previous_price=2450.0, timestamp=1234567890.0)
        assert update.direction == "flat"

    def test_to_dict(self):
        update = PriceUpdate(code="토마토", price=190.50, previous_price=190.00, timestamp=1234567890.0)
        result = update.to_dict()

        assert result["code"] == "토마토"
        assert result["price"] == 190.50
        assert result["previous_price"] == 190.00
        assert result["timestamp"] == 1234567890.0
        assert result["change"] == 0.50
        assert result["change_percent"] == 0.2632  # (0.50 / 190.00) * 100
        assert result["direction"] == "up"

    def test_immutability(self):
        update = PriceUpdate(code="토마토", price=190.50, previous_price=190.00, timestamp=1234567890.0)

        with pytest.raises(AttributeError):
            update.price = 200.00  # Should raise error
