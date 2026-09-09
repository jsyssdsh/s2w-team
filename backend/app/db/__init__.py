"""Database layer for S2W (uldungbuldung farm AI).

Public API is grouped by entity; see db/schema.sql for the underlying tables
and db/seed.sql for the demo dataset that reproduces planning/SPEC.md's
example tables.

    init_db                          - Create tables (no data)
    seed_demo_data                   - Load db/seed.sql's demo rows
    get_connection                   - Get an async SQLite connection
    set_db_path / get_db_path        - Override/read the DB file path

    create_user / get_user / list_users

    create_crop / get_crop / get_crop_by_name / list_crops
    upsert_crop_optimal_range / get_crop_optimal_ranges

    create_farmland / get_farmland / search_farmlands / update_farmland_status

    create_smart_farm / get_smart_farm / list_smart_farms_by_farmer / list_smart_farms
    get_smart_farm_by_farmland
    insert_sensor_reading / get_latest_sensor_readings / get_sensor_readings_range

    create_shipment_plan / get_shipment_plan / get_shipment_plans_by_farmer
    list_shipment_plans / update_shipment_plan_status

    insert_market_price / get_price_history

    create_wholesaler / get_wholesaler / list_wholesalers
    create_wholesaler_crop_offer / get_wholesaler_candidates
    upsert_wholesaler_inventory / get_total_wholesaler_inventory

    create_retailer / get_retailer / list_retailers
    create_retailer_crop_demand / get_retailer_candidates_for_grade
    get_total_retailer_demand

    get_total_planned_shipment_kg / get_supply_demand_balance

    create_transaction / get_transaction / list_transactions_for_shipment
    update_transaction_status

    create_recommendation / get_recommendation / get_recommendations_for_subject
    record_recommendation_outcome

    insert_chat_message / get_chat_history
"""

from .connection import get_connection, get_db_path, init_db, seed_demo_data, set_db_path
from .repository import (
    create_crop,
    create_farmland,
    create_recommendation,
    create_retailer,
    create_retailer_crop_demand,
    create_shipment_plan,
    create_smart_farm,
    create_transaction,
    create_user,
    create_wholesaler,
    create_wholesaler_crop_offer,
    get_chat_history,
    get_crop,
    get_crop_by_name,
    get_crop_optimal_ranges,
    get_farmland,
    get_latest_sensor_readings,
    get_price_history,
    get_recommendation,
    get_recommendations_for_subject,
    get_retailer,
    get_retailer_candidates_for_grade,
    get_sensor_readings_range,
    get_shipment_plan,
    get_shipment_plans_by_farmer,
    get_smart_farm,
    get_smart_farm_by_farmland,
    get_supply_demand_balance,
    get_total_planned_shipment_kg,
    get_total_retailer_demand,
    get_total_wholesaler_inventory,
    get_transaction,
    get_user,
    get_wholesaler,
    get_wholesaler_candidates,
    insert_chat_message,
    insert_market_price,
    insert_sensor_reading,
    list_crops,
    list_retailers,
    list_shipment_plans,
    list_smart_farms,
    list_smart_farms_by_farmer,
    list_transactions_for_shipment,
    list_users,
    list_wholesalers,
    record_recommendation_outcome,
    search_farmlands,
    update_farmland_status,
    update_shipment_plan_status,
    update_transaction_status,
    upsert_crop_optimal_range,
    upsert_wholesaler_inventory,
)
from .schema import (
    CHAT_MESSAGE_ROLES,
    FARMLAND_CONDITION_GRADES,
    FARMLAND_STATUSES,
    RECOMMENDATION_OUTCOMES,
    RECOMMENDATION_TYPES,
    RETAILER_TYPES,
    SENSOR_METRICS,
    SHIPMENT_GRADES,
    SHIPMENT_STATUSES,
    TRANSACTION_COUNTERPARTY_TYPES,
    TRANSACTION_STATUSES,
    USER_ROLES,
)

__all__ = [
    "init_db",
    "seed_demo_data",
    "get_connection",
    "get_db_path",
    "set_db_path",
    "create_user",
    "get_user",
    "list_users",
    "create_crop",
    "get_crop",
    "get_crop_by_name",
    "list_crops",
    "upsert_crop_optimal_range",
    "get_crop_optimal_ranges",
    "create_farmland",
    "get_farmland",
    "search_farmlands",
    "update_farmland_status",
    "create_smart_farm",
    "get_smart_farm",
    "list_smart_farms_by_farmer",
    "list_smart_farms",
    "get_smart_farm_by_farmland",
    "insert_sensor_reading",
    "get_latest_sensor_readings",
    "get_sensor_readings_range",
    "create_shipment_plan",
    "get_shipment_plan",
    "get_shipment_plans_by_farmer",
    "list_shipment_plans",
    "update_shipment_plan_status",
    "insert_market_price",
    "get_price_history",
    "create_wholesaler",
    "get_wholesaler",
    "list_wholesalers",
    "create_wholesaler_crop_offer",
    "get_wholesaler_candidates",
    "upsert_wholesaler_inventory",
    "get_total_wholesaler_inventory",
    "create_retailer",
    "get_retailer",
    "list_retailers",
    "create_retailer_crop_demand",
    "get_retailer_candidates_for_grade",
    "get_total_retailer_demand",
    "get_total_planned_shipment_kg",
    "get_supply_demand_balance",
    "create_transaction",
    "get_transaction",
    "list_transactions_for_shipment",
    "update_transaction_status",
    "create_recommendation",
    "get_recommendation",
    "get_recommendations_for_subject",
    "record_recommendation_outcome",
    "insert_chat_message",
    "get_chat_history",
    "USER_ROLES",
    "RETAILER_TYPES",
    "FARMLAND_CONDITION_GRADES",
    "FARMLAND_STATUSES",
    "SENSOR_METRICS",
    "SHIPMENT_GRADES",
    "SHIPMENT_STATUSES",
    "TRANSACTION_COUNTERPARTY_TYPES",
    "TRANSACTION_STATUSES",
    "RECOMMENDATION_TYPES",
    "RECOMMENDATION_OUTCOMES",
    "CHAT_MESSAGE_ROLES",
]
