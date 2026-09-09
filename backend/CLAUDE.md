# Backend — Developer Guide

## Project Setup

```bash
cd backend
uv sync --extra dev   # Install all dependencies including test/lint tools
```

## Live Data Streams (crop prices, smart-farm sensors)

The streaming subsystem lives in `app/market/`. Use these imports:

```python
from app.market import PriceCache, PriceUpdate, create_stream_router
from app.market import CropPriceSimulator, CropPriceStream
from app.market import SensorSimulator, SensorStream, make_code, metric_of
```

There is no real-time produce/IoT data provider integrated (aT auctions
settle daily; there's no ESP32 hardware in this environment) -- both live
feeds are demo-only random-walk simulators, kept separate from the
deterministic forecasting/recommendation math in `app/services/`.

### Core Types

- **`PriceUpdate`** — Immutable dataclass: `code` (a crop name, or
  `"{smart_farm_id}:{metric}"` for a sensor series), `price`, `previous_price`,
  `timestamp`, plus properties `change`, `change_percent`, `direction`
  ("up"/"down"/"flat"), and `to_dict()` for JSON/SSE serialization.

- **`PriceCache`** — Thread-safe in-memory store, one instance per stream
  (crop prices and sensor readings use separate caches so codes can't
  collide). Key methods:
  - `update(code, price, timestamp=None) -> PriceUpdate`
  - `get(code) -> PriceUpdate | None`
  - `get_price(code) -> float | None`
  - `get_all() -> dict[str, PriceUpdate]`
  - `remove(code)`
  - `version` property — monotonic counter, increments on every update (for SSE change detection)

- **`CropPriceSimulator` / `CropPriceStream`** — mean-reverting random walk
  around each crop's seed wholesale price (`app/market/seed_data.py`).
  `CropPriceStream(cache).start(crop_names)` runs it as a background task.

- **`SensorSimulator` / `SensorStream`** — mean-reverting random walk per
  `(smart_farm_id, metric)` series. `SensorStream(cache).start({code: value})`
  runs it as a background task. Use `make_code(farm_id, metric)` /
  `metric_of(code)` to build/parse series codes.

### SSE Streaming

```python
from app.market import create_stream_router

# path/tag let you mount independent streams off /api/stream
app.include_router(create_stream_router(price_cache, path="/prices", tag="crop-prices"))
app.include_router(create_stream_router(sensor_cache, path="/sensors", tag="sensors"))
```

### Seed Data

Crop wholesale price baselines and per-crop volatility are in
`app/market/seed_data.py`. Sensor evaluation against a crop's optimal range
(not simulation) lives in `app/services/sensors.py`, driven by
`crop_optimal_ranges` rows from the DB.

## Running Tests

```bash
uv run --extra dev pytest -v              # All tests
uv run --extra dev pytest --cov=app       # With coverage
uv run --extra dev ruff check app/ tests/ # Lint
```

## Demo

```bash
uv run market_data_demo.py   # Live terminal dashboard with simulated prices
```
