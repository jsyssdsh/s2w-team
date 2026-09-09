"""Seed values for the live crop-price simulator.

Matches db/seed.sql's most recent market_prices row per crop so the live SSE
stream starts from the same numbers the REST endpoints show. sigma is a
per-tick relative volatility (produce wholesale prices move far more slowly
than stock prices -- this is deliberately much smaller than the old stock
simulator's per-ticker sigma).
"""

# KRW per kg, matching the latest row per crop in db/seed.sql's market_prices.
SEED_CROP_PRICES: dict[str, float] = {
    "토마토": 2320.0,
    "양파": 950.0,
    "딸기": 9800.0,
}

# Per-crop relative volatility per tick. Unlisted crops fall back to DEFAULT_SIGMA.
CROP_SIGMA: dict[str, float] = {
    "토마토": 0.003,
    "양파": 0.004,
    "딸기": 0.005,
}
DEFAULT_SIGMA = 0.003

# How strongly price drifts back toward its seed baseline each tick (0..1).
# Keeps the live stream wandering around a realistic wholesale price instead
# of drifting away permanently like an unconstrained random walk would.
REVERSION_RATE = 0.05
