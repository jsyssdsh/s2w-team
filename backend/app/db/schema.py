"""Schema/seed SQL loading and domain constants for the S2W database.

The SQL itself lives in db/schema.sql and db/seed.sql at the repo root (not
duplicated as Python strings) so there is exactly one place that defines the
tables. See db/schema.sql for column-level documentation and units.
"""

from functools import lru_cache
from pathlib import Path

# backend/app/db/schema.py -> parents[3] is the repo root.
_REPO_ROOT = Path(__file__).resolve().parents[3]
SCHEMA_SQL_PATH = _REPO_ROOT / "db" / "schema.sql"
SEED_SQL_PATH = _REPO_ROOT / "db" / "seed.sql"


@lru_cache(maxsize=1)
def get_schema_sql() -> str:
    """Return the full DDL script. Cached since the file never changes at runtime."""
    return SCHEMA_SQL_PATH.read_text(encoding="utf-8")


@lru_cache(maxsize=1)
def get_seed_sql() -> str:
    """Return the demo seed data script."""
    return SEED_SQL_PATH.read_text(encoding="utf-8")


# Enum-like values kept in one place so callers don't hand-roll string
# literals that could drift from the CHECK constraints in db/schema.sql.
USER_ROLES = ("farmer", "wholesaler", "retailer", "landowner")
RETAILER_TYPES = ("대형마트", "학교급식", "가공업체", "지역음식점", "기타")
FARMLAND_CONDITION_GRADES = ("최상", "양호", "개선필요")
FARMLAND_STATUSES = ("idle", "matched", "operating")
SENSOR_METRICS = ("temperature", "humidity", "soil_moisture", "light")
SHIPMENT_GRADES = ("특상품", "상품", "규격외", "판매기한임박")
SHIPMENT_STATUSES = ("planned", "shipped", "sold", "cancelled")
TRANSACTION_COUNTERPARTY_TYPES = ("wholesaler", "retailer")
TRANSACTION_STATUSES = ("requested", "accepted", "rejected", "completed", "cancelled")
RECOMMENDATION_TYPES = (
    "price_forecast",
    "wholesaler_match",
    "retailer_match",
    "supply_risk_alert",
    "farmland_match",
)
RECOMMENDATION_OUTCOMES = ("selected", "rejected")
CHAT_MESSAGE_ROLES = ("user", "assistant", "tool")
