"""Cross-entity lookups that compose app.db's DAL but aren't a single call.

Most cross-farmer/cross-entity queries now live directly in app.db
(list_smart_farms, get_smart_farm_by_farmland, list_shipment_plans) --
database-engineer added those once asked. What's left here is lookups that
are still route-specific enough not to belong in the generic DAL: matching a
free-text crop/counterparty name from a chat message to a specific shipment
plan or business, which is chat-tool logic, not a reusable query shape.
"""

from __future__ import annotations

from typing import Any

from app.db import get_shipment_plans_by_farmer, list_retailers, list_wholesalers


async def find_farmer_shipment_plan_for_crop(
    farmer_user_id: str, crop_id: str, status: str = "planned"
) -> dict[str, Any] | None:
    """A farmer's most recently created open shipment plan for one crop.

    Used by the chat assistant's create_trade_request tool, which only knows
    a crop name -- not which specific shipment plan the user means.
    """
    plans = await get_shipment_plans_by_farmer(farmer_user_id, status=status)
    matching = [p for p in plans if p["crop_id"] == crop_id]
    if not matching:
        return None
    return max(matching, key=lambda p: p["created_at"])


def _normalize(text: str) -> str:
    """Lowercase and drop whitespace so chat phrasing like '도매처B' still
    matches a DB name stored as '도매처 B'."""
    return text.strip().lower().replace(" ", "")


async def find_counterparty_by_name(name: str) -> tuple[str, dict[str, Any]] | None:
    """Find a wholesaler or retailer whose name contains `name` (case-insensitive,
    whitespace-insensitive).

    Returns (counterparty_type, row) or None. Wholesalers are checked first
    since SPEC 5.2's trade-request flow is farmer -> wholesaler by default.
    """
    needle = _normalize(name)
    for wholesaler in await list_wholesalers():
        if needle in _normalize(wholesaler["name"]):
            return "wholesaler", wholesaler
    for retailer in await list_retailers():
        if needle in _normalize(retailer["name"]):
            return "retailer", retailer
    return None
