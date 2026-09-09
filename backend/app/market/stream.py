"""SSE streaming endpoint factory for live series (crop prices, sensor readings)."""

from __future__ import annotations

import asyncio
import json
import logging
from collections.abc import AsyncGenerator

from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse

from .cache import PriceCache

logger = logging.getLogger(__name__)


def create_stream_router(
    price_cache: PriceCache, path: str = "/prices", tag: str = "streaming"
) -> APIRouter:
    """Create an SSE streaming router bound to one PriceCache.

    This factory pattern lets us inject the PriceCache without globals, and
    lets the caller mount independent streams (crop prices, sensor readings)
    at different paths off the same /api/stream prefix.
    """
    router = APIRouter(prefix="/api/stream", tags=[tag])

    @router.get(path)
    async def stream(request: Request) -> StreamingResponse:
        """SSE endpoint for live updates.

        Streams every tracked series every ~500ms. The client connects with
        EventSource and receives events in the format:

            data: {"토마토": {"code": "토마토", "price": 2450.0, ...}, ...}

        Includes a retry directive so the browser auto-reconnects on
        disconnection (EventSource built-in behavior).
        """
        return StreamingResponse(
            _generate_events(price_cache, request),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",  # Disable nginx buffering if proxied
            },
        )

    return router


async def _generate_events(
    price_cache: PriceCache,
    request: Request,
    interval: float = 0.5,
) -> AsyncGenerator[str, None]:
    """Async generator that yields SSE-formatted events.

    Sends all values every `interval` seconds. Stops when the client
    disconnects (detected via request.is_disconnected()).
    """
    # Tell the client to retry after 1 second if the connection drops
    yield "retry: 1000\n\n"

    last_version = -1
    client_ip = request.client.host if request.client else "unknown"
    logger.info("SSE client connected: %s", client_ip)

    try:
        while True:
            # Check for client disconnect
            if await request.is_disconnected():
                logger.info("SSE client disconnected: %s", client_ip)
                break

            current_version = price_cache.version
            if current_version != last_version:
                last_version = current_version
                values = price_cache.get_all()

                if values:
                    data = {code: update.to_dict() for code, update in values.items()}
                    payload = json.dumps(data, ensure_ascii=False)
                    yield f"data: {payload}\n\n"

            await asyncio.sleep(interval)
    except asyncio.CancelledError:
        logger.info("SSE stream cancelled for: %s", client_ip)
