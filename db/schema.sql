-- S2W (uldungbuldung farm AI) database schema.
--
-- Domain: idle farmland matching, smart-farm sensor monitoring, crop shipment
-- planning, wholesaler/retailer distribution matching, market price history,
-- and AI recommendation logging. See planning/SPEC.md sections 5-7 for the
-- business rules this schema supports.
--
-- Conventions:
--   * All timestamps are UTC ISO-8601 strings (e.g. "2026-08-08T02:00:00+00:00").
--   * Money columns are whole KRW (won) integers -- the domain never deals in
--     fractional won, so REAL would just invite rounding drift.
--   * Quantity columns are REAL kilograms unless the column name says otherwise
--     (farmland area is in pyeong, per SPEC 5.6).
--   * Recommendation "subject"/"target" columns are polymorphic (they point at
--     different tables depending on recommendation_type) so they are plain TEXT
--     ids without a FOREIGN KEY -- SQLite cannot express a conditional FK, and a
--     junction table per type would be overkill for a prototype. Application
--     code is responsible for interpreting them alongside *_type.

PRAGMA foreign_keys = ON;

-- ---------------------------------------------------------------------------
-- Users and role-specific profiles
-- ---------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY,
    role TEXT NOT NULL CHECK (role IN ('farmer', 'wholesaler', 'retailer', 'landowner')),
    name TEXT NOT NULL,
    phone TEXT,
    email TEXT,
    region TEXT,
    created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);

-- A wholesaler is a distribution company, not just a user account -- it needs
-- its own row so it can be referenced by offers/inventory/transactions even
-- before it has a linked login.
CREATE TABLE IF NOT EXISTS wholesalers (
    id TEXT PRIMARY KEY,
    user_id TEXT REFERENCES users(id),
    name TEXT NOT NULL,
    region TEXT,
    location TEXT,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS retailers (
    id TEXT PRIMARY KEY,
    user_id TEXT REFERENCES users(id),
    name TEXT NOT NULL,
    -- retailer_type drives which shipment grade AI recommends it for (SPEC 5.3).
    retailer_type TEXT NOT NULL CHECK (
        retailer_type IN ('대형마트', '학교급식', '가공업체', '지역음식점', '기타')
    ),
    region TEXT,
    location TEXT,
    delivery_terms TEXT,
    created_at TEXT NOT NULL
);

-- ---------------------------------------------------------------------------
-- Crops (defined early: referenced by optimal ranges, offers, demand, prices)
-- ---------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS crops (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    unit TEXT NOT NULL DEFAULT 'kg',
    created_at TEXT NOT NULL
);

-- ---------------------------------------------------------------------------
-- Idle farmland and smart farms
-- ---------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS farmlands (
    id TEXT PRIMARY KEY,
    owner_user_id TEXT NOT NULL REFERENCES users(id),
    address TEXT NOT NULL,
    region TEXT,
    latitude REAL,
    longitude REAL,
    area_pyeong REAL NOT NULL,
    monthly_rent_krw INTEGER NOT NULL,
    has_water_access INTEGER NOT NULL DEFAULT 0 CHECK (has_water_access IN (0, 1)),
    has_cold_storage_access INTEGER NOT NULL DEFAULT 0 CHECK (has_cold_storage_access IN (0, 1)),
    distance_to_wholesaler_km REAL,
    soil_status TEXT,
    -- Drives the map color coding in SPEC 4.4 (green/yellow/red).
    condition_grade TEXT NOT NULL CHECK (condition_grade IN ('최상', '양호', '개선필요')),
    -- idle: listed, unmatched. matched: farmer selected, not yet planted.
    -- operating: an active smart_farms row exists on this land.
    status TEXT NOT NULL DEFAULT 'idle' CHECK (status IN ('idle', 'matched', 'operating')),
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_farmlands_status ON farmlands(status);
CREATE INDEX IF NOT EXISTS idx_farmlands_region ON farmlands(region);

CREATE TABLE IF NOT EXISTS smart_farms (
    id TEXT PRIMARY KEY,
    farmland_id TEXT NOT NULL REFERENCES farmlands(id),
    farmer_user_id TEXT NOT NULL REFERENCES users(id),
    farm_type TEXT NOT NULL,
    operation_start_date TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_smart_farms_farmer ON smart_farms(farmer_user_id);

-- Per-crop acceptable sensor ranges, used to flag out-of-range readings and
-- drive auto-control (SPEC 5.5). light_max is nullable because the spec only
-- defines a floor ("설정 기준 이상").
CREATE TABLE IF NOT EXISTS crop_optimal_ranges (
    id TEXT PRIMARY KEY,
    crop_id TEXT NOT NULL REFERENCES crops(id),
    metric TEXT NOT NULL CHECK (metric IN ('temperature', 'humidity', 'soil_moisture', 'light')),
    min_value REAL,
    max_value REAL,
    unit TEXT NOT NULL,
    UNIQUE (crop_id, metric)
);

CREATE TABLE IF NOT EXISTS sensor_readings (
    id TEXT PRIMARY KEY,
    smart_farm_id TEXT NOT NULL REFERENCES smart_farms(id),
    metric TEXT NOT NULL CHECK (metric IN ('temperature', 'humidity', 'soil_moisture', 'light')),
    value REAL NOT NULL,
    unit TEXT NOT NULL,
    measured_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_sensor_readings_farm_metric_time
    ON sensor_readings(smart_farm_id, metric, measured_at);

-- ---------------------------------------------------------------------------
-- Shipment plans, market prices
-- ---------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS shipment_plans (
    id TEXT PRIMARY KEY,
    farmer_user_id TEXT NOT NULL REFERENCES users(id),
    smart_farm_id TEXT REFERENCES smart_farms(id),
    crop_id TEXT NOT NULL REFERENCES crops(id),
    -- Denormalized from the farmland/smart_farm chain so region-level supply
    -- aggregation (SPEC 5.4) does not need a multi-table join per row.
    region TEXT,
    expected_yield_kg REAL NOT NULL,
    planned_shipment_date TEXT NOT NULL,
    grade TEXT NOT NULL CHECK (grade IN ('특상품', '상품', '규격외', '판매기한임박')),
    status TEXT NOT NULL DEFAULT 'planned'
        CHECK (status IN ('planned', 'shipped', 'sold', 'cancelled')),
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_shipment_plans_farmer ON shipment_plans(farmer_user_id);
CREATE INDEX IF NOT EXISTS idx_shipment_plans_crop_region ON shipment_plans(crop_id, region);
CREATE INDEX IF NOT EXISTS idx_shipment_plans_status ON shipment_plans(status);

CREATE TABLE IF NOT EXISTS market_prices (
    id TEXT PRIMARY KEY,
    crop_id TEXT NOT NULL REFERENCES crops(id),
    price_date TEXT NOT NULL,
    region TEXT,
    wholesale_price_krw_per_kg INTEGER NOT NULL,
    transaction_volume_kg REAL,
    shipment_volume_kg REAL,
    UNIQUE (crop_id, price_date, region)
);

CREATE INDEX IF NOT EXISTS idx_market_prices_crop_date ON market_prices(crop_id, price_date);

-- ---------------------------------------------------------------------------
-- Wholesaler offers and inventory
-- ---------------------------------------------------------------------------

-- What a wholesaler is willing to pay/handle for one crop right now. transport
-- and commission are stored alongside distance because SPEC 5.2's demo table
-- gives pre-computed transport figures per offer rather than a formula --
-- distance_km is kept as the "산정 근거" (calculation basis) for reference.
CREATE TABLE IF NOT EXISTS wholesaler_crop_offers (
    id TEXT PRIMARY KEY,
    wholesaler_id TEXT NOT NULL REFERENCES wholesalers(id),
    crop_id TEXT NOT NULL REFERENCES crops(id),
    purchase_unit_price_krw_per_kg INTEGER NOT NULL,
    purchase_capacity_kg REAL NOT NULL,
    distance_km REAL,
    transport_cost_krw INTEGER NOT NULL,
    commission_rate REAL NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_wholesaler_offers_crop ON wholesaler_crop_offers(crop_id);

CREATE TABLE IF NOT EXISTS wholesaler_inventories (
    id TEXT PRIMARY KEY,
    wholesaler_id TEXT NOT NULL REFERENCES wholesalers(id),
    crop_id TEXT NOT NULL REFERENCES crops(id),
    quantity_kg REAL NOT NULL,
    as_of_date TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_wholesaler_inventories_crop ON wholesaler_inventories(crop_id);

CREATE TABLE IF NOT EXISTS retailer_crop_demands (
    id TEXT PRIMARY KEY,
    retailer_id TEXT NOT NULL REFERENCES retailers(id),
    crop_id TEXT NOT NULL REFERENCES crops(id),
    -- Which shipment grade this demand line wants, so grade-based matching
    -- (SPEC 5.3) can join directly against shipment_plans.grade.
    grade TEXT CHECK (grade IN ('특상품', '상품', '규격외', '판매기한임박')),
    demand_quantity_kg REAL NOT NULL,
    as_of_date TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_retailer_demands_crop ON retailer_crop_demands(crop_id);

-- ---------------------------------------------------------------------------
-- AI recommendations and their eventual outcome
-- ---------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS ai_recommendations (
    id TEXT PRIMARY KEY,
    recommendation_type TEXT NOT NULL CHECK (recommendation_type IN (
        'price_forecast', 'wholesaler_match', 'retailer_match',
        'supply_risk_alert', 'farmland_match'
    )),
    -- Polymorphic reference to what this recommendation is about
    -- (e.g. a shipment_plans row, or a users row doing a farmland search).
    subject_type TEXT NOT NULL,
    subject_id TEXT NOT NULL,
    -- Polymorphic reference to what is being recommended
    -- (e.g. a wholesalers row, a farmlands row, or a plain shipment date string).
    target_type TEXT NOT NULL,
    target_id TEXT NOT NULL,
    score REAL,
    rank INTEGER,
    rationale TEXT NOT NULL,
    -- Structured extras that do not fit the fixed columns above (e.g. the
    -- supply/demand breakdown table for a supply_risk_alert). JSON text.
    metadata TEXT,
    created_at TEXT NOT NULL,
    -- NULL until the user acts on it; feeds SPEC 6.2's recommendation-improvement loop.
    outcome TEXT CHECK (outcome IN ('selected', 'rejected')),
    decided_at TEXT
);

CREATE INDEX IF NOT EXISTS idx_ai_recommendations_subject
    ON ai_recommendations(subject_type, subject_id);
CREATE INDEX IF NOT EXISTS idx_ai_recommendations_type ON ai_recommendations(recommendation_type);

-- ---------------------------------------------------------------------------
-- Transactions (farmer <-> wholesaler <-> retailer)
-- ---------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS transactions (
    id TEXT PRIMARY KEY,
    shipment_plan_id TEXT NOT NULL REFERENCES shipment_plans(id),
    -- Exactly one of these identifies the counterparty; counterparty_type says which.
    wholesaler_id TEXT REFERENCES wholesalers(id),
    retailer_id TEXT REFERENCES retailers(id),
    counterparty_type TEXT NOT NULL CHECK (counterparty_type IN ('wholesaler', 'retailer')),
    -- Links back to the recommendation that produced this transaction, so the
    -- chosen outcome can be fed back into future recommendation ranking
    -- (SPEC 6.2 "유통 매칭 기능").
    recommendation_id TEXT REFERENCES ai_recommendations(id),
    quantity_kg REAL NOT NULL,
    unit_price_krw_per_kg INTEGER NOT NULL,
    transport_cost_krw INTEGER NOT NULL DEFAULT 0,
    commission_krw INTEGER NOT NULL DEFAULT 0,
    net_profit_krw INTEGER,
    status TEXT NOT NULL DEFAULT 'requested'
        CHECK (status IN ('requested', 'accepted', 'rejected', 'completed', 'cancelled')),
    requested_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_transactions_shipment_plan ON transactions(shipment_plan_id);
CREATE INDEX IF NOT EXISTS idx_transactions_status ON transactions(status);

-- ---------------------------------------------------------------------------
-- Chat assistant history
-- ---------------------------------------------------------------------------

-- One row per chat turn. session_id is caller-assigned (the backend decides
-- what identifies a conversation, e.g. per browser session or per user) and
-- is intentionally not a foreign key to users -- an anonymous/pre-login
-- session should still be able to chat. 'tool' rows record a tool call the
-- assistant made mid-turn (SPEC's trade-executing chat assistant); content
-- holds its JSON-serialized {name, arguments, result, error}. actions is a
-- separate optional JSON blob on 'assistant' rows for the structured actions
-- (e.g. ToolCallOutcome list) the frontend renders alongside that reply --
-- kept distinct from content so the visible chat text and the machine-
-- readable action log don't have to be parsed apart on every read.
CREATE TABLE IF NOT EXISTS chat_messages (
    id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL,
    role TEXT NOT NULL CHECK (role IN ('user', 'assistant', 'tool')),
    content TEXT NOT NULL,
    actions TEXT,
    created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_chat_messages_session ON chat_messages(session_id, created_at);
