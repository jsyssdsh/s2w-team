"""Typed data-access functions for every S2W entity.

Grouped to mirror db/schema.sql. Every query is parameterized -- never
string-interpolate a value into SQL here.
"""

import json
import uuid
from datetime import datetime, timezone
from typing import Any

from .connection import get_connection


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _uuid(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:12]}"


# --- Users -------------------------------------------------------------


async def create_user(
    role: str,
    name: str,
    phone: str | None = None,
    email: str | None = None,
    region: str | None = None,
) -> dict[str, Any]:
    """Create a user with one of the four platform roles."""
    user = {
        "id": _uuid("user"),
        "role": role,
        "name": name,
        "phone": phone,
        "email": email,
        "region": region,
        "created_at": _now(),
    }
    db = await get_connection()
    try:
        await db.execute(
            "INSERT INTO users (id, role, name, phone, email, region, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (user["id"], role, name, phone, email, region, user["created_at"]),
        )
        await db.commit()
        return user
    finally:
        await db.close()


async def get_user(user_id: str) -> dict[str, Any] | None:
    """Get a user by id."""
    db = await get_connection()
    try:
        cursor = await db.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        row = await cursor.fetchone()
        return dict(row) if row else None
    finally:
        await db.close()


async def list_users(role: str | None = None) -> list[dict[str, Any]]:
    """List users, optionally filtered by role."""
    db = await get_connection()
    try:
        if role is not None:
            cursor = await db.execute(
                "SELECT * FROM users WHERE role = ? ORDER BY created_at", (role,)
            )
        else:
            cursor = await db.execute("SELECT * FROM users ORDER BY created_at")
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]
    finally:
        await db.close()


# --- Crops ---------------------------------------------------------------


async def create_crop(name: str, unit: str = "kg") -> dict[str, Any]:
    """Create a crop master record."""
    crop = {"id": _uuid("crop"), "name": name, "unit": unit, "created_at": _now()}
    db = await get_connection()
    try:
        await db.execute(
            "INSERT INTO crops (id, name, unit, created_at) VALUES (?, ?, ?, ?)",
            (crop["id"], name, unit, crop["created_at"]),
        )
        await db.commit()
        return crop
    finally:
        await db.close()


async def get_crop(crop_id: str) -> dict[str, Any] | None:
    """Get a crop by id."""
    db = await get_connection()
    try:
        cursor = await db.execute("SELECT * FROM crops WHERE id = ?", (crop_id,))
        row = await cursor.fetchone()
        return dict(row) if row else None
    finally:
        await db.close()


async def get_crop_by_name(name: str) -> dict[str, Any] | None:
    """Get a crop by its display name (e.g. '토마토')."""
    db = await get_connection()
    try:
        cursor = await db.execute("SELECT * FROM crops WHERE name = ?", (name,))
        row = await cursor.fetchone()
        return dict(row) if row else None
    finally:
        await db.close()


async def list_crops() -> list[dict[str, Any]]:
    """List all crops."""
    db = await get_connection()
    try:
        cursor = await db.execute("SELECT * FROM crops ORDER BY name")
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]
    finally:
        await db.close()


async def upsert_crop_optimal_range(
    crop_id: str,
    metric: str,
    min_value: float | None,
    max_value: float | None,
    unit: str,
) -> dict[str, Any]:
    """Create or replace a crop's acceptable range for one sensor metric."""
    db = await get_connection()
    try:
        cursor = await db.execute(
            "SELECT id FROM crop_optimal_ranges WHERE crop_id = ? AND metric = ?",
            (crop_id, metric),
        )
        existing = await cursor.fetchone()
        range_id = existing["id"] if existing else _uuid("range")

        await db.execute(
            "INSERT INTO crop_optimal_ranges (id, crop_id, metric, min_value, max_value, unit) "
            "VALUES (?, ?, ?, ?, ?, ?) "
            "ON CONFLICT(crop_id, metric) DO UPDATE SET "
            "min_value = excluded.min_value, max_value = excluded.max_value, unit = excluded.unit",
            (range_id, crop_id, metric, min_value, max_value, unit),
        )
        await db.commit()
        return {
            "id": range_id,
            "crop_id": crop_id,
            "metric": metric,
            "min_value": min_value,
            "max_value": max_value,
            "unit": unit,
        }
    finally:
        await db.close()


async def get_crop_optimal_ranges(crop_id: str) -> list[dict[str, Any]]:
    """Get all sensor metric ranges defined for a crop."""
    db = await get_connection()
    try:
        cursor = await db.execute(
            "SELECT * FROM crop_optimal_ranges WHERE crop_id = ?", (crop_id,)
        )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]
    finally:
        await db.close()


# --- Farmlands -------------------------------------------------------------


async def create_farmland(
    owner_user_id: str,
    address: str,
    area_pyeong: float,
    monthly_rent_krw: int,
    has_water_access: bool,
    has_cold_storage_access: bool,
    condition_grade: str,
    region: str | None = None,
    latitude: float | None = None,
    longitude: float | None = None,
    distance_to_wholesaler_km: float | None = None,
    soil_status: str | None = None,
    status: str = "idle",
) -> dict[str, Any]:
    """Register a farmland listing."""
    now = _now()
    farmland = {
        "id": _uuid("farmland"),
        "owner_user_id": owner_user_id,
        "address": address,
        "region": region,
        "latitude": latitude,
        "longitude": longitude,
        "area_pyeong": area_pyeong,
        "monthly_rent_krw": monthly_rent_krw,
        "has_water_access": int(has_water_access),
        "has_cold_storage_access": int(has_cold_storage_access),
        "distance_to_wholesaler_km": distance_to_wholesaler_km,
        "soil_status": soil_status,
        "condition_grade": condition_grade,
        "status": status,
        "created_at": now,
        "updated_at": now,
    }
    db = await get_connection()
    try:
        await db.execute(
            "INSERT INTO farmlands (id, owner_user_id, address, region, latitude, longitude, "
            "area_pyeong, monthly_rent_krw, has_water_access, has_cold_storage_access, "
            "distance_to_wholesaler_km, soil_status, condition_grade, status, created_at, updated_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                farmland["id"], owner_user_id, address, region, latitude, longitude,
                area_pyeong, monthly_rent_krw, farmland["has_water_access"],
                farmland["has_cold_storage_access"], distance_to_wholesaler_km,
                soil_status, condition_grade, status, now, now,
            ),
        )
        await db.commit()
        return farmland
    finally:
        await db.close()


async def get_farmland(farmland_id: str) -> dict[str, Any] | None:
    """Get a farmland listing by id."""
    db = await get_connection()
    try:
        cursor = await db.execute("SELECT * FROM farmlands WHERE id = ?", (farmland_id,))
        row = await cursor.fetchone()
        return dict(row) if row else None
    finally:
        await db.close()


async def search_farmlands(
    min_area_pyeong: float | None = None,
    max_area_pyeong: float | None = None,
    max_monthly_rent_krw: int | None = None,
    require_water_access: bool | None = None,
    require_cold_storage_access: bool | None = None,
    region: str | None = None,
    status: str | None = None,
) -> list[dict[str, Any]]:
    """Search farmlands by area/rent/water/cold-storage/region/status filters.

    Supports SPEC 5.6 (희망 면적/예산/조건에 맞는 유휴농지 탐색). All filters
    are optional and combined with AND; omitted filters are not applied.
    """
    clauses: list[str] = []
    params: list[Any] = []

    if min_area_pyeong is not None:
        clauses.append("area_pyeong >= ?")
        params.append(min_area_pyeong)
    if max_area_pyeong is not None:
        clauses.append("area_pyeong <= ?")
        params.append(max_area_pyeong)
    if max_monthly_rent_krw is not None:
        clauses.append("monthly_rent_krw <= ?")
        params.append(max_monthly_rent_krw)
    if require_water_access:
        clauses.append("has_water_access = 1")
    if require_cold_storage_access:
        clauses.append("has_cold_storage_access = 1")
    if region is not None:
        clauses.append("region = ?")
        params.append(region)
    if status is not None:
        clauses.append("status = ?")
        params.append(status)

    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    db = await get_connection()
    try:
        cursor = await db.execute(
            f"SELECT * FROM farmlands {where} ORDER BY distance_to_wholesaler_km", params
        )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]
    finally:
        await db.close()


async def update_farmland_status(farmland_id: str, status: str) -> dict[str, Any] | None:
    """Transition a farmland between idle / matched / operating."""
    db = await get_connection()
    try:
        now = _now()
        await db.execute(
            "UPDATE farmlands SET status = ?, updated_at = ? WHERE id = ?",
            (status, now, farmland_id),
        )
        await db.commit()
        cursor = await db.execute("SELECT * FROM farmlands WHERE id = ?", (farmland_id,))
        row = await cursor.fetchone()
        return dict(row) if row else None
    finally:
        await db.close()


# --- Smart farms and sensors ------------------------------------------------


async def create_smart_farm(
    farmland_id: str, farmer_user_id: str, farm_type: str, operation_start_date: str
) -> dict[str, Any]:
    """Register a smart farm operating on a (now-occupied) farmland."""
    farm = {
        "id": _uuid("farm"),
        "farmland_id": farmland_id,
        "farmer_user_id": farmer_user_id,
        "farm_type": farm_type,
        "operation_start_date": operation_start_date,
        "created_at": _now(),
    }
    db = await get_connection()
    try:
        await db.execute(
            "INSERT INTO smart_farms (id, farmland_id, farmer_user_id, farm_type, "
            "operation_start_date, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            (
                farm["id"], farmland_id, farmer_user_id, farm_type,
                operation_start_date, farm["created_at"],
            ),
        )
        await db.commit()
        return farm
    finally:
        await db.close()


async def get_smart_farm(smart_farm_id: str) -> dict[str, Any] | None:
    """Get a smart farm by id."""
    db = await get_connection()
    try:
        cursor = await db.execute("SELECT * FROM smart_farms WHERE id = ?", (smart_farm_id,))
        row = await cursor.fetchone()
        return dict(row) if row else None
    finally:
        await db.close()


async def list_smart_farms_by_farmer(farmer_user_id: str) -> list[dict[str, Any]]:
    """List all smart farms operated by a farmer."""
    db = await get_connection()
    try:
        cursor = await db.execute(
            "SELECT * FROM smart_farms WHERE farmer_user_id = ? ORDER BY operation_start_date",
            (farmer_user_id,),
        )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]
    finally:
        await db.close()


async def list_smart_farms() -> list[dict[str, Any]]:
    """List every smart farm. Used by the sensor SSE loop to poll all active farms."""
    db = await get_connection()
    try:
        cursor = await db.execute("SELECT * FROM smart_farms ORDER BY operation_start_date")
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]
    finally:
        await db.close()


async def get_smart_farm_by_farmland(farmland_id: str) -> dict[str, Any] | None:
    """Get the smart farm operating on a farmland, if any (SPEC 4.5 farmland detail view).

    A farmland has at most one active smart farm at a time in this model, so
    the most recently started one is returned if somehow more than one exists.
    """
    db = await get_connection()
    try:
        cursor = await db.execute(
            "SELECT * FROM smart_farms WHERE farmland_id = ? "
            "ORDER BY operation_start_date DESC LIMIT 1",
            (farmland_id,),
        )
        row = await cursor.fetchone()
        return dict(row) if row else None
    finally:
        await db.close()


async def insert_sensor_reading(
    smart_farm_id: str,
    metric: str,
    value: float,
    unit: str,
    measured_at: str | None = None,
) -> dict[str, Any]:
    """Record one sensor measurement. measured_at defaults to now (UTC)."""
    reading = {
        "id": _uuid("reading"),
        "smart_farm_id": smart_farm_id,
        "metric": metric,
        "value": value,
        "unit": unit,
        "measured_at": measured_at or _now(),
    }
    db = await get_connection()
    try:
        await db.execute(
            "INSERT INTO sensor_readings (id, smart_farm_id, metric, value, unit, measured_at) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (
                reading["id"], smart_farm_id, metric, value, unit,
                reading["measured_at"],
            ),
        )
        await db.commit()
        return reading
    finally:
        await db.close()


async def get_latest_sensor_readings(smart_farm_id: str) -> dict[str, dict[str, Any]]:
    """Get the most recent reading per metric for a smart farm, keyed by metric."""
    db = await get_connection()
    try:
        cursor = await db.execute(
            "SELECT * FROM sensor_readings WHERE smart_farm_id = ? "
            "AND measured_at = (SELECT MAX(measured_at) FROM sensor_readings sr2 "
            "WHERE sr2.smart_farm_id = sensor_readings.smart_farm_id AND sr2.metric = sensor_readings.metric) "
            "ORDER BY metric",
            (smart_farm_id,),
        )
        rows = await cursor.fetchall()
        return {row["metric"]: dict(row) for row in rows}
    finally:
        await db.close()


async def get_sensor_readings_range(
    smart_farm_id: str, metric: str, start: str, end: str
) -> list[dict[str, Any]]:
    """Get a time series of one metric between two UTC ISO-8601 timestamps (inclusive)."""
    db = await get_connection()
    try:
        cursor = await db.execute(
            "SELECT * FROM sensor_readings WHERE smart_farm_id = ? AND metric = ? "
            "AND measured_at >= ? AND measured_at <= ? ORDER BY measured_at",
            (smart_farm_id, metric, start, end),
        )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]
    finally:
        await db.close()


# --- Shipment plans ----------------------------------------------------


async def create_shipment_plan(
    farmer_user_id: str,
    crop_id: str,
    expected_yield_kg: float,
    planned_shipment_date: str,
    grade: str,
    smart_farm_id: str | None = None,
    region: str | None = None,
    status: str = "planned",
) -> dict[str, Any]:
    """Register a crop shipment plan."""
    now = _now()
    plan = {
        "id": _uuid("shipment"),
        "farmer_user_id": farmer_user_id,
        "smart_farm_id": smart_farm_id,
        "crop_id": crop_id,
        "region": region,
        "expected_yield_kg": expected_yield_kg,
        "planned_shipment_date": planned_shipment_date,
        "grade": grade,
        "status": status,
        "created_at": now,
        "updated_at": now,
    }
    db = await get_connection()
    try:
        await db.execute(
            "INSERT INTO shipment_plans (id, farmer_user_id, smart_farm_id, crop_id, region, "
            "expected_yield_kg, planned_shipment_date, grade, status, created_at, updated_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                plan["id"], farmer_user_id, smart_farm_id, crop_id, region,
                expected_yield_kg, planned_shipment_date, grade, status, now, now,
            ),
        )
        await db.commit()
        return plan
    finally:
        await db.close()


async def get_shipment_plan(shipment_plan_id: str) -> dict[str, Any] | None:
    """Get a shipment plan by id."""
    db = await get_connection()
    try:
        cursor = await db.execute(
            "SELECT * FROM shipment_plans WHERE id = ?", (shipment_plan_id,)
        )
        row = await cursor.fetchone()
        return dict(row) if row else None
    finally:
        await db.close()


async def get_shipment_plans_by_farmer(
    farmer_user_id: str, status: str | None = None
) -> list[dict[str, Any]]:
    """List a farmer's shipment plans, optionally filtered by status."""
    db = await get_connection()
    try:
        if status is not None:
            cursor = await db.execute(
                "SELECT * FROM shipment_plans WHERE farmer_user_id = ? AND status = ? "
                "ORDER BY planned_shipment_date",
                (farmer_user_id, status),
            )
        else:
            cursor = await db.execute(
                "SELECT * FROM shipment_plans WHERE farmer_user_id = ? "
                "ORDER BY planned_shipment_date",
                (farmer_user_id,),
            )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]
    finally:
        await db.close()


async def list_shipment_plans(
    crop_id: str | None = None,
    region: str | None = None,
    status: str | None = None,
) -> list[dict[str, Any]]:
    """List shipment plans across farmers, filtered by crop/region/status.

    Backs cross-farmer views like the wholesaler dashboard's "AI 추천 농가
    리스트" (SPEC 4.3), which needs every farmer's plans for a crop rather
    than one farmer's plans.
    """
    clauses: list[str] = []
    params: list[Any] = []
    if crop_id is not None:
        clauses.append("crop_id = ?")
        params.append(crop_id)
    if region is not None:
        clauses.append("region = ?")
        params.append(region)
    if status is not None:
        clauses.append("status = ?")
        params.append(status)
    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""

    db = await get_connection()
    try:
        cursor = await db.execute(
            f"SELECT * FROM shipment_plans {where} ORDER BY planned_shipment_date", params
        )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]
    finally:
        await db.close()


async def update_shipment_plan_status(
    shipment_plan_id: str, status: str
) -> dict[str, Any] | None:
    """Transition a shipment plan's status."""
    db = await get_connection()
    try:
        now = _now()
        await db.execute(
            "UPDATE shipment_plans SET status = ?, updated_at = ? WHERE id = ?",
            (status, now, shipment_plan_id),
        )
        await db.commit()
        cursor = await db.execute(
            "SELECT * FROM shipment_plans WHERE id = ?", (shipment_plan_id,)
        )
        row = await cursor.fetchone()
        return dict(row) if row else None
    finally:
        await db.close()


# --- Market prices -------------------------------------------------------


async def insert_market_price(
    crop_id: str,
    price_date: str,
    wholesale_price_krw_per_kg: int,
    transaction_volume_kg: float | None = None,
    shipment_volume_kg: float | None = None,
    region: str | None = None,
) -> dict[str, Any]:
    """Record one day's wholesale price point for a crop."""
    price = {
        "id": _uuid("price"),
        "crop_id": crop_id,
        "price_date": price_date,
        "region": region,
        "wholesale_price_krw_per_kg": wholesale_price_krw_per_kg,
        "transaction_volume_kg": transaction_volume_kg,
        "shipment_volume_kg": shipment_volume_kg,
    }
    db = await get_connection()
    try:
        await db.execute(
            "INSERT INTO market_prices (id, crop_id, price_date, region, "
            "wholesale_price_krw_per_kg, transaction_volume_kg, shipment_volume_kg) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                price["id"], crop_id, price_date, region, wholesale_price_krw_per_kg,
                transaction_volume_kg, shipment_volume_kg,
            ),
        )
        await db.commit()
        return price
    finally:
        await db.close()


async def get_price_history(
    crop_id: str,
    region: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
) -> list[dict[str, Any]]:
    """Get a crop's price history, oldest first, optionally scoped by region/date range."""
    clauses = ["crop_id = ?"]
    params: list[Any] = [crop_id]

    if region is not None:
        clauses.append("region = ?")
        params.append(region)
    if start_date is not None:
        clauses.append("price_date >= ?")
        params.append(start_date)
    if end_date is not None:
        clauses.append("price_date <= ?")
        params.append(end_date)

    db = await get_connection()
    try:
        cursor = await db.execute(
            f"SELECT * FROM market_prices WHERE {' AND '.join(clauses)} ORDER BY price_date",
            params,
        )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]
    finally:
        await db.close()


# --- Wholesalers -----------------------------------------------------------


async def create_wholesaler(
    name: str,
    user_id: str | None = None,
    region: str | None = None,
    location: str | None = None,
) -> dict[str, Any]:
    """Register a wholesaler."""
    wholesaler = {
        "id": _uuid("wholesaler"),
        "user_id": user_id,
        "name": name,
        "region": region,
        "location": location,
        "created_at": _now(),
    }
    db = await get_connection()
    try:
        await db.execute(
            "INSERT INTO wholesalers (id, user_id, name, region, location, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (wholesaler["id"], user_id, name, region, location, wholesaler["created_at"]),
        )
        await db.commit()
        return wholesaler
    finally:
        await db.close()


async def get_wholesaler(wholesaler_id: str) -> dict[str, Any] | None:
    """Get a wholesaler by id."""
    db = await get_connection()
    try:
        cursor = await db.execute("SELECT * FROM wholesalers WHERE id = ?", (wholesaler_id,))
        row = await cursor.fetchone()
        return dict(row) if row else None
    finally:
        await db.close()


async def list_wholesalers(region: str | None = None) -> list[dict[str, Any]]:
    """List wholesalers, optionally filtered by region."""
    db = await get_connection()
    try:
        if region is not None:
            cursor = await db.execute(
                "SELECT * FROM wholesalers WHERE region = ? ORDER BY name", (region,)
            )
        else:
            cursor = await db.execute("SELECT * FROM wholesalers ORDER BY name")
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]
    finally:
        await db.close()


async def create_wholesaler_crop_offer(
    wholesaler_id: str,
    crop_id: str,
    purchase_unit_price_krw_per_kg: int,
    purchase_capacity_kg: float,
    transport_cost_krw: int,
    commission_rate: float = 0.0,
    distance_km: float | None = None,
) -> dict[str, Any]:
    """Register what a wholesaler is currently offering to pay/handle for a crop."""
    offer = {
        "id": _uuid("offer"),
        "wholesaler_id": wholesaler_id,
        "crop_id": crop_id,
        "purchase_unit_price_krw_per_kg": purchase_unit_price_krw_per_kg,
        "purchase_capacity_kg": purchase_capacity_kg,
        "distance_km": distance_km,
        "transport_cost_krw": transport_cost_krw,
        "commission_rate": commission_rate,
        "created_at": _now(),
    }
    db = await get_connection()
    try:
        await db.execute(
            "INSERT INTO wholesaler_crop_offers (id, wholesaler_id, crop_id, "
            "purchase_unit_price_krw_per_kg, purchase_capacity_kg, distance_km, "
            "transport_cost_krw, commission_rate, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                offer["id"], wholesaler_id, crop_id, purchase_unit_price_krw_per_kg,
                purchase_capacity_kg, distance_km, transport_cost_krw, commission_rate,
                offer["created_at"],
            ),
        )
        await db.commit()
        return offer
    finally:
        await db.close()


async def get_wholesaler_candidates(
    crop_id: str, min_capacity_kg: float | None = None, region: str | None = None
) -> list[dict[str, Any]]:
    """List wholesaler offers for a crop that can take at least min_capacity_kg.

    Supports SPEC 5.2 (매입단가/구매가능량/운송비/수수료로 후보 도매처 비교). Each row
    joins the offer with its wholesaler so callers get name/location/region
    without a second query. Net profit is intentionally not computed here --
    it depends on the farmer's own quantity and belongs in the AI/recommendation
    layer, not the data-access layer.
    """
    clauses = ["o.crop_id = ?"]
    params: list[Any] = [crop_id]

    if min_capacity_kg is not None:
        clauses.append("o.purchase_capacity_kg >= ?")
        params.append(min_capacity_kg)
    if region is not None:
        clauses.append("w.region = ?")
        params.append(region)

    db = await get_connection()
    try:
        cursor = await db.execute(
            "SELECT o.*, w.name AS wholesaler_name, w.region AS wholesaler_region, "
            "w.location AS wholesaler_location FROM wholesaler_crop_offers o "
            f"JOIN wholesalers w ON w.id = o.wholesaler_id WHERE {' AND '.join(clauses)} "
            "ORDER BY o.purchase_unit_price_krw_per_kg DESC",
            params,
        )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]
    finally:
        await db.close()


async def upsert_wholesaler_inventory(
    wholesaler_id: str, crop_id: str, quantity_kg: float, as_of_date: str
) -> dict[str, Any]:
    """Record a wholesaler's on-hand stock of a crop as of a given date."""
    db = await get_connection()
    try:
        cursor = await db.execute(
            "SELECT id FROM wholesaler_inventories WHERE wholesaler_id = ? AND crop_id = ?",
            (wholesaler_id, crop_id),
        )
        existing = await cursor.fetchone()
        inventory_id = existing["id"] if existing else _uuid("inventory")
        now = _now()

        if existing:
            await db.execute(
                "UPDATE wholesaler_inventories SET quantity_kg = ?, as_of_date = ? WHERE id = ?",
                (quantity_kg, as_of_date, inventory_id),
            )
        else:
            await db.execute(
                "INSERT INTO wholesaler_inventories (id, wholesaler_id, crop_id, quantity_kg, "
                "as_of_date, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                (inventory_id, wholesaler_id, crop_id, quantity_kg, as_of_date, now),
            )
        await db.commit()
        return {
            "id": inventory_id,
            "wholesaler_id": wholesaler_id,
            "crop_id": crop_id,
            "quantity_kg": quantity_kg,
            "as_of_date": as_of_date,
        }
    finally:
        await db.close()


async def get_total_wholesaler_inventory(crop_id: str, region: str | None = None) -> float:
    """Sum all wholesalers' on-hand stock of a crop (used in supply-risk analysis)."""
    db = await get_connection()
    try:
        if region is not None:
            cursor = await db.execute(
                "SELECT COALESCE(SUM(i.quantity_kg), 0) AS total FROM wholesaler_inventories i "
                "JOIN wholesalers w ON w.id = i.wholesaler_id "
                "WHERE i.crop_id = ? AND w.region = ?",
                (crop_id, region),
            )
        else:
            cursor = await db.execute(
                "SELECT COALESCE(SUM(quantity_kg), 0) AS total FROM wholesaler_inventories "
                "WHERE crop_id = ?",
                (crop_id,),
            )
        row = await cursor.fetchone()
        return float(row["total"])
    finally:
        await db.close()


# --- Retailers -------------------------------------------------------------


async def create_retailer(
    name: str,
    retailer_type: str,
    user_id: str | None = None,
    region: str | None = None,
    location: str | None = None,
    delivery_terms: str | None = None,
) -> dict[str, Any]:
    """Register a retailer/sales outlet (대형마트/학교급식/가공업체/지역음식점/기타)."""
    retailer = {
        "id": _uuid("retailer"),
        "user_id": user_id,
        "name": name,
        "retailer_type": retailer_type,
        "region": region,
        "location": location,
        "delivery_terms": delivery_terms,
        "created_at": _now(),
    }
    db = await get_connection()
    try:
        await db.execute(
            "INSERT INTO retailers (id, user_id, name, retailer_type, region, location, "
            "delivery_terms, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (
                retailer["id"], user_id, name, retailer_type, region, location,
                delivery_terms, retailer["created_at"],
            ),
        )
        await db.commit()
        return retailer
    finally:
        await db.close()


async def get_retailer(retailer_id: str) -> dict[str, Any] | None:
    """Get a retailer by id."""
    db = await get_connection()
    try:
        cursor = await db.execute("SELECT * FROM retailers WHERE id = ?", (retailer_id,))
        row = await cursor.fetchone()
        return dict(row) if row else None
    finally:
        await db.close()


async def list_retailers(
    retailer_type: str | None = None, region: str | None = None
) -> list[dict[str, Any]]:
    """List retailers, optionally filtered by type and/or region."""
    clauses: list[str] = []
    params: list[Any] = []
    if retailer_type is not None:
        clauses.append("retailer_type = ?")
        params.append(retailer_type)
    if region is not None:
        clauses.append("region = ?")
        params.append(region)
    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""

    db = await get_connection()
    try:
        cursor = await db.execute(f"SELECT * FROM retailers {where} ORDER BY name", params)
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]
    finally:
        await db.close()


async def create_retailer_crop_demand(
    retailer_id: str,
    crop_id: str,
    demand_quantity_kg: float,
    as_of_date: str,
    grade: str | None = None,
) -> dict[str, Any]:
    """Register a retailer's demand for a crop (optionally scoped to a shipment grade)."""
    demand = {
        "id": _uuid("demand"),
        "retailer_id": retailer_id,
        "crop_id": crop_id,
        "grade": grade,
        "demand_quantity_kg": demand_quantity_kg,
        "as_of_date": as_of_date,
        "created_at": _now(),
    }
    db = await get_connection()
    try:
        await db.execute(
            "INSERT INTO retailer_crop_demands (id, retailer_id, crop_id, grade, "
            "demand_quantity_kg, as_of_date, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                demand["id"], retailer_id, crop_id, grade, demand_quantity_kg,
                as_of_date, demand["created_at"],
            ),
        )
        await db.commit()
        return demand
    finally:
        await db.close()


async def get_retailer_candidates_for_grade(crop_id: str, grade: str) -> list[dict[str, Any]]:
    """List retailers whose demand for a crop matches a specific shipment grade.

    Supports SPEC 5.3 (등급별 판매처 매칭 -- 특상품/상품/규격외/판매기한임박).
    """
    db = await get_connection()
    try:
        cursor = await db.execute(
            "SELECT d.*, r.name AS retailer_name, r.retailer_type, r.region AS retailer_region, "
            "r.location AS retailer_location, r.delivery_terms FROM retailer_crop_demands d "
            "JOIN retailers r ON r.id = d.retailer_id "
            "WHERE d.crop_id = ? AND d.grade = ? ORDER BY d.demand_quantity_kg DESC",
            (crop_id, grade),
        )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]
    finally:
        await db.close()


async def get_total_retailer_demand(crop_id: str, region: str | None = None) -> float:
    """Sum all retailer demand for a crop (used in supply-risk analysis)."""
    db = await get_connection()
    try:
        if region is not None:
            cursor = await db.execute(
                "SELECT COALESCE(SUM(d.demand_quantity_kg), 0) AS total "
                "FROM retailer_crop_demands d JOIN retailers r ON r.id = d.retailer_id "
                "WHERE d.crop_id = ? AND r.region = ?",
                (crop_id, region),
            )
        else:
            cursor = await db.execute(
                "SELECT COALESCE(SUM(demand_quantity_kg), 0) AS total "
                "FROM retailer_crop_demands WHERE crop_id = ?",
                (crop_id,),
            )
        row = await cursor.fetchone()
        return float(row["total"])
    finally:
        await db.close()


# --- Supply / demand aggregation --------------------------------------------


async def get_total_planned_shipment_kg(
    crop_id: str, region: str | None = None, status: str = "planned"
) -> float:
    """Sum farmers' planned shipment volume for a crop (SPEC 5.4's '농가 출하 예정량')."""
    db = await get_connection()
    try:
        if region is not None:
            cursor = await db.execute(
                "SELECT COALESCE(SUM(expected_yield_kg), 0) AS total FROM shipment_plans "
                "WHERE crop_id = ? AND region = ? AND status = ?",
                (crop_id, region, status),
            )
        else:
            cursor = await db.execute(
                "SELECT COALESCE(SUM(expected_yield_kg), 0) AS total FROM shipment_plans "
                "WHERE crop_id = ? AND status = ?",
                (crop_id, status),
            )
        row = await cursor.fetchone()
        return float(row["total"])
    finally:
        await db.close()


async def get_supply_demand_balance(
    crop_id: str, region: str | None = None
) -> dict[str, float]:
    """Compute the region/crop supply-vs-demand snapshot behind SPEC 5.4's alert table.

    total_supply_kg = farmer_planned_kg + wholesaler_inventory_kg
    excess_supply_kg = total_supply_kg - retailer_demand_kg (negative means a shortfall)
    """
    farmer_planned_kg = await get_total_planned_shipment_kg(crop_id, region=region)
    wholesaler_inventory_kg = await get_total_wholesaler_inventory(crop_id, region=region)
    retailer_demand_kg = await get_total_retailer_demand(crop_id, region=region)
    total_supply_kg = farmer_planned_kg + wholesaler_inventory_kg

    return {
        "farmer_planned_kg": farmer_planned_kg,
        "wholesaler_inventory_kg": wholesaler_inventory_kg,
        "total_supply_kg": total_supply_kg,
        "retailer_demand_kg": retailer_demand_kg,
        "excess_supply_kg": total_supply_kg - retailer_demand_kg,
    }


# --- Transactions ------------------------------------------------------


async def create_transaction(
    shipment_plan_id: str,
    counterparty_type: str,
    quantity_kg: float,
    unit_price_krw_per_kg: int,
    wholesaler_id: str | None = None,
    retailer_id: str | None = None,
    recommendation_id: str | None = None,
    transport_cost_krw: int = 0,
    commission_krw: int = 0,
    net_profit_krw: int | None = None,
    status: str = "requested",
) -> dict[str, Any]:
    """Create a transaction (or transaction request) between a shipment plan and a counterparty."""
    now = _now()
    txn = {
        "id": _uuid("txn"),
        "shipment_plan_id": shipment_plan_id,
        "wholesaler_id": wholesaler_id,
        "retailer_id": retailer_id,
        "counterparty_type": counterparty_type,
        "recommendation_id": recommendation_id,
        "quantity_kg": quantity_kg,
        "unit_price_krw_per_kg": unit_price_krw_per_kg,
        "transport_cost_krw": transport_cost_krw,
        "commission_krw": commission_krw,
        "net_profit_krw": net_profit_krw,
        "status": status,
        "requested_at": now,
        "updated_at": now,
    }
    db = await get_connection()
    try:
        await db.execute(
            "INSERT INTO transactions (id, shipment_plan_id, wholesaler_id, retailer_id, "
            "counterparty_type, recommendation_id, quantity_kg, unit_price_krw_per_kg, "
            "transport_cost_krw, commission_krw, net_profit_krw, status, requested_at, updated_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                txn["id"], shipment_plan_id, wholesaler_id, retailer_id, counterparty_type,
                recommendation_id, quantity_kg, unit_price_krw_per_kg, transport_cost_krw,
                commission_krw, net_profit_krw, status, now, now,
            ),
        )
        await db.commit()
        return txn
    finally:
        await db.close()


async def get_transaction(transaction_id: str) -> dict[str, Any] | None:
    """Get a transaction by id."""
    db = await get_connection()
    try:
        cursor = await db.execute("SELECT * FROM transactions WHERE id = ?", (transaction_id,))
        row = await cursor.fetchone()
        return dict(row) if row else None
    finally:
        await db.close()


async def list_transactions_for_shipment(shipment_plan_id: str) -> list[dict[str, Any]]:
    """List all transactions/requests tied to a shipment plan."""
    db = await get_connection()
    try:
        cursor = await db.execute(
            "SELECT * FROM transactions WHERE shipment_plan_id = ? ORDER BY requested_at",
            (shipment_plan_id,),
        )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]
    finally:
        await db.close()


async def update_transaction_status(
    transaction_id: str, status: str
) -> dict[str, Any] | None:
    """Transition a transaction through requested -> accepted/rejected -> completed/cancelled."""
    db = await get_connection()
    try:
        now = _now()
        await db.execute(
            "UPDATE transactions SET status = ?, updated_at = ? WHERE id = ?",
            (status, now, transaction_id),
        )
        await db.commit()
        cursor = await db.execute("SELECT * FROM transactions WHERE id = ?", (transaction_id,))
        row = await cursor.fetchone()
        return dict(row) if row else None
    finally:
        await db.close()


# --- AI recommendations ---------------------------------------------------


async def create_recommendation(
    recommendation_type: str,
    subject_type: str,
    subject_id: str,
    target_type: str,
    target_id: str,
    rationale: str,
    score: float | None = None,
    rank: int | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Log one AI recommendation with its score, rank, and rationale.

    metadata is stored as a JSON string; pass a plain dict and it will be
    serialized. Retrieval functions deserialize it back into a dict.
    """
    metadata_json = json.dumps(metadata, ensure_ascii=False) if metadata is not None else None
    now = _now()
    rec = {
        "id": _uuid("rec"),
        "recommendation_type": recommendation_type,
        "subject_type": subject_type,
        "subject_id": subject_id,
        "target_type": target_type,
        "target_id": target_id,
        "score": score,
        "rank": rank,
        "rationale": rationale,
        "metadata": metadata,
        "created_at": now,
        "outcome": None,
        "decided_at": None,
    }
    db = await get_connection()
    try:
        await db.execute(
            "INSERT INTO ai_recommendations (id, recommendation_type, subject_type, subject_id, "
            "target_type, target_id, score, rank, rationale, metadata, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                rec["id"], recommendation_type, subject_type, subject_id, target_type,
                target_id, score, rank, rationale, metadata_json, now,
            ),
        )
        await db.commit()
        return rec
    finally:
        await db.close()


def _deserialize_recommendation(row: dict[str, Any]) -> dict[str, Any]:
    """Parse the metadata JSON column back into a dict (or None)."""
    row = dict(row)
    if row.get("metadata"):
        row["metadata"] = json.loads(row["metadata"])
    return row


async def get_recommendations_for_subject(
    subject_type: str, subject_id: str, recommendation_type: str | None = None
) -> list[dict[str, Any]]:
    """List recommendations about a subject (e.g. a shipment plan), best rank first."""
    db = await get_connection()
    try:
        if recommendation_type is not None:
            cursor = await db.execute(
                "SELECT * FROM ai_recommendations WHERE subject_type = ? AND subject_id = ? "
                "AND recommendation_type = ? ORDER BY rank IS NULL, rank",
                (subject_type, subject_id, recommendation_type),
            )
        else:
            cursor = await db.execute(
                "SELECT * FROM ai_recommendations WHERE subject_type = ? AND subject_id = ? "
                "ORDER BY rank IS NULL, rank",
                (subject_type, subject_id),
            )
        rows = await cursor.fetchall()
        return [_deserialize_recommendation(dict(row)) for row in rows]
    finally:
        await db.close()


async def get_recommendation(recommendation_id: str) -> dict[str, Any] | None:
    """Get a single recommendation by id."""
    db = await get_connection()
    try:
        cursor = await db.execute(
            "SELECT * FROM ai_recommendations WHERE id = ?", (recommendation_id,)
        )
        row = await cursor.fetchone()
        return _deserialize_recommendation(dict(row)) if row else None
    finally:
        await db.close()


async def record_recommendation_outcome(
    recommendation_id: str, outcome: str
) -> dict[str, Any] | None:
    """Record whether the user selected or rejected a recommendation.

    This is the feedback signal SPEC 6.2 calls for ("실제 거래 선택 결과를
    다시 DB에 저장해 추천 기준을 개선"); it does not itself change any
    ranking logic, it just persists the ground truth for later use.
    """
    db = await get_connection()
    try:
        now = _now()
        await db.execute(
            "UPDATE ai_recommendations SET outcome = ?, decided_at = ? WHERE id = ?",
            (outcome, now, recommendation_id),
        )
        await db.commit()
        cursor = await db.execute(
            "SELECT * FROM ai_recommendations WHERE id = ?", (recommendation_id,)
        )
        row = await cursor.fetchone()
        return _deserialize_recommendation(dict(row)) if row else None
    finally:
        await db.close()


# --- Chat assistant history --------------------------------------------


_DEFAULT_CHAT_SESSION_ID = "default"


async def insert_chat_message(
    role: str,
    content: str,
    actions: list[Any] | dict[str, Any] | None = None,
    session_id: str = _DEFAULT_CHAT_SESSION_ID,
    created_at: str | None = None,
) -> dict[str, Any]:
    """Store one chat turn. role is 'user', 'assistant', or 'tool'.

    For 'tool' rows, content is expected to be a JSON string (e.g. a
    serialized ToolCallOutcome) -- this layer stores it as opaque text either way.
    actions is a separate optional JSON-serializable payload (e.g. the list of
    ToolCallOutcome the frontend renders next to an 'assistant' reply); pass a
    plain list/dict and it is serialized for you, then parsed back on read.

    session_id defaults to a single shared "default" session so callers that
    don't have a per-user/per-conversation identifier yet (no auth wired up)
    can ignore it entirely. Pass an explicit session_id once the caller has
    something to key chat threads on (e.g. per logged-in user) -- the schema
    already supports multiple concurrent sessions, this default just avoids
    forcing that decision on every call site today.
    """
    actions_json = json.dumps(actions, ensure_ascii=False) if actions is not None else None
    message = {
        "id": _uuid("msg"),
        "session_id": session_id,
        "role": role,
        "content": content,
        "actions": actions,
        "created_at": created_at or _now(),
    }
    db = await get_connection()
    try:
        await db.execute(
            "INSERT INTO chat_messages (id, session_id, role, content, actions, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (message["id"], session_id, role, content, actions_json, message["created_at"]),
        )
        await db.commit()
        return message
    finally:
        await db.close()


def _deserialize_chat_message(row: dict[str, Any]) -> dict[str, Any]:
    """Parse the actions JSON column back into a list/dict (or None)."""
    row = dict(row)
    if row.get("actions"):
        row["actions"] = json.loads(row["actions"])
    return row


async def get_chat_history(
    limit: int = 50, session_id: str = _DEFAULT_CHAT_SESSION_ID
) -> list[dict[str, Any]]:
    """Get the most recent messages in a session, oldest-first.

    Mirrors the shape run_chat_assistant expects for its `history` argument
    (each row has at least "role" and "content"). See insert_chat_message for
    why session_id defaults to a single shared session.
    """
    db = await get_connection()
    try:
        cursor = await db.execute(
            "SELECT * FROM chat_messages WHERE session_id = ? "
            "ORDER BY created_at DESC LIMIT ?",
            (session_id, limit),
        )
        rows = await cursor.fetchall()
        return [_deserialize_chat_message(dict(row)) for row in reversed(rows)]
    finally:
        await db.close()
