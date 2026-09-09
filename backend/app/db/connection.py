"""Database connection management with lazy initialization."""

import os
from pathlib import Path

import aiosqlite

from .schema import get_schema_sql, get_seed_sql

_REPO_ROOT = Path(__file__).resolve().parents[3]
_DEFAULT_DB_PATH = str(_REPO_ROOT / "db" / "s2w.db")

_DB_PATH: str | None = None


def get_db_path() -> str:
    """Return the configured database path."""
    global _DB_PATH
    if _DB_PATH is None:
        _DB_PATH = os.environ.get("S2W_DB_PATH", _DEFAULT_DB_PATH)
    return _DB_PATH


def set_db_path(path: str) -> None:
    """Override the database path (for testing)."""
    global _DB_PATH
    _DB_PATH = path


async def get_connection() -> aiosqlite.Connection:
    """Open a connection to the database."""
    db = await aiosqlite.connect(get_db_path())
    db.row_factory = aiosqlite.Row
    await db.execute("PRAGMA journal_mode=WAL")
    await db.execute("PRAGMA foreign_keys=ON")
    return db


async def init_db() -> None:
    """Create tables if they do not already exist. Does not insert any data."""
    db = await get_connection()
    try:
        await db.executescript(get_schema_sql())
        await db.commit()
    finally:
        await db.close()


async def seed_demo_data() -> None:
    """Load db/seed.sql's demo data into the current database.

    Kept separate from init_db so unit tests can exercise a bare schema
    without dragging in demo rows. Not idempotent -- seed.sql uses fixed ids
    and will raise a UNIQUE constraint error if run twice against the same
    database, which is intentional (it signals the caller is re-seeding a
    database that already has demo data).
    """
    db = await get_connection()
    try:
        await db.executescript(get_seed_sql())
        await db.commit()
    finally:
        await db.close()
