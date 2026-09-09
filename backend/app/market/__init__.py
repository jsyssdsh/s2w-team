"""Live-data streaming subsystem for S2W (crop wholesale prices, smart-farm sensors).

Public API:
    PriceUpdate          - Immutable value snapshot dataclass
    PriceCache           - Thread-safe in-memory store, one per live series
    create_stream_router - FastAPI router factory for one SSE endpoint

    CropPriceSimulator, CropPriceStream           - live crop price feed
    SensorSimulator, SensorStream, make_code, metric_of - live sensor feed
"""

from .cache import PriceCache
from .crop_price_simulator import CropPriceSimulator, CropPriceStream
from .models import PriceUpdate
from .sensor_simulator import SensorSimulator, SensorStream, make_code, metric_of
from .stream import create_stream_router

__all__ = [
    "PriceUpdate",
    "PriceCache",
    "create_stream_router",
    "CropPriceSimulator",
    "CropPriceStream",
    "SensorSimulator",
    "SensorStream",
    "make_code",
    "metric_of",
]
