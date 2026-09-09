-- Demo seed data for S2W. Every scenario table in planning/SPEC.md section 5
-- has a corresponding row set here so the platform can display the exact
-- numbers used in the spec (tomato wholesaler comparison, tomato grade-based
-- retailer matching, tomato price forecast, onion supply-risk alert,
-- strawberry farmland comparison, tomato sensor auto-control).
--
-- IDs are deterministic slugs (not UUIDs) so this file is idempotent-ish for
-- a fresh database and easy to cross-reference while reading it.

-- ---------------------------------------------------------------------------
-- Users
-- ---------------------------------------------------------------------------

INSERT INTO users (id, role, name, phone, email, region, created_at) VALUES
    ('user-farmer-kim', 'farmer', '김농부', '010-1000-2000', 'kim.farmer@example.com', '충남 논산시', '2026-01-05T00:00:00+00:00'),
    ('user-farmer-lee', 'farmer', '이청년', '010-1000-2001', 'lee.farmer@example.com', '충남 논산시', '2026-01-10T00:00:00+00:00'),
    ('user-farmer-park', 'farmer', '박농부', '010-1000-2002', 'park.farmer@example.com', '충남 논산시', '2026-01-10T00:00:00+00:00'),
    ('user-farmer-choi', 'farmer', '최농부', '010-1000-2003', 'choi.farmer@example.com', '충남 논산시', '2026-01-10T00:00:00+00:00'),
    ('user-landowner-a', 'landowner', '정지주', '010-2000-3000', 'jung.landowner@example.com', '충남 논산시', '2026-01-01T00:00:00+00:00'),
    ('user-landowner-b', 'landowner', '한지주', '010-2000-3001', 'han.landowner@example.com', '충남 논산시', '2026-01-01T00:00:00+00:00'),
    ('user-landowner-c', 'landowner', '윤지주', '010-2000-3002', 'yoon.landowner@example.com', '충남 논산시', '2026-01-01T00:00:00+00:00'),
    ('user-landowner-existing', 'landowner', '강지주', '010-2000-3003', 'kang.landowner@example.com', '충남 논산시', '2026-01-01T00:00:00+00:00'),
    ('user-wholesaler-a', 'wholesaler', '도매처 A 담당자', '010-3000-4000', 'a@wholesale.example.com', '충남 논산시', '2026-01-01T00:00:00+00:00'),
    ('user-wholesaler-b', 'wholesaler', '도매처 B 담당자', '010-3000-4001', 'b@wholesale.example.com', '충남 논산시', '2026-01-01T00:00:00+00:00'),
    ('user-wholesaler-c', 'wholesaler', '도매처 C 담당자', '010-3000-4002', 'c@wholesale.example.com', '충남 논산시', '2026-01-01T00:00:00+00:00'),
    ('user-retailer-mart', 'retailer', '대형마트 구매팀', '010-4000-5000', 'mart@retail.example.com', '충남 논산시', '2026-01-01T00:00:00+00:00'),
    ('user-retailer-school', 'retailer', '학교급식지원센터', '010-4000-5001', 'school@retail.example.com', '충남 논산시', '2026-01-01T00:00:00+00:00'),
    ('user-retailer-factory', 'retailer', '소스가공업체', '010-4000-5002', 'factory@retail.example.com', '충남 논산시', '2026-01-01T00:00:00+00:00'),
    ('user-retailer-restaurant', 'retailer', '지역 음식점 조합', '010-4000-5003', 'restaurant@retail.example.com', '충남 논산시', '2026-01-01T00:00:00+00:00');

-- ---------------------------------------------------------------------------
-- Crops
-- ---------------------------------------------------------------------------

INSERT INTO crops (id, name, unit, created_at) VALUES
    ('crop-tomato', '토마토', 'kg', '2026-01-01T00:00:00+00:00'),
    ('crop-onion', '양파', 'kg', '2026-01-01T00:00:00+00:00'),
    ('crop-strawberry', '딸기', 'kg', '2026-01-01T00:00:00+00:00');

INSERT INTO crop_optimal_ranges (id, crop_id, metric, min_value, max_value, unit) VALUES
    ('range-tomato-temp', 'crop-tomato', 'temperature', 22, 27, 'celsius'),
    ('range-tomato-humidity', 'crop-tomato', 'humidity', 60, 75, 'percent'),
    ('range-tomato-soil', 'crop-tomato', 'soil_moisture', 35, 55, 'percent'),
    -- Spec only defines a floor ("설정 기준 이상"); 20000 lux is the baseline
    -- that the 82%/101% readings in SPEC 5.5 are expressed against.
    ('range-tomato-light', 'crop-tomato', 'light', 20000, NULL, 'lux');

-- ---------------------------------------------------------------------------
-- Farmland A/B/C -- SPEC 5.6 strawberry farmland comparison
-- ---------------------------------------------------------------------------

-- latitude/longitude are approximate points scattered around the named
-- 읍 (Ganggyeong-eup / Yeonmu-eup, Nonsan) for map display -- not surveyed
-- parcel coordinates, just plausible enough to place four distinct pins.
INSERT INTO farmlands (
    id, owner_user_id, address, region, latitude, longitude, area_pyeong, monthly_rent_krw,
    has_water_access, has_cold_storage_access, distance_to_wholesaler_km,
    soil_status, condition_grade, status, created_at, updated_at
) VALUES
    ('farmland-a', 'user-landowner-a', '충남 논산시 강경읍 A지구', '충남 논산시', 36.1605, 126.8830, 900, 650000,
        1, 1, 24, '양토, 배수 양호', '최상', 'idle', '2026-02-01T00:00:00+00:00', '2026-02-01T00:00:00+00:00'),
    ('farmland-b', 'user-landowner-b', '충남 논산시 강경읍 B지구', '충남 논산시', 36.1548, 126.8905, 1000, 550000,
        1, 0, 38, '양토, 관수 필요', '양호', 'idle', '2026-02-01T00:00:00+00:00', '2026-02-01T00:00:00+00:00'),
    ('farmland-c', 'user-landowner-c', '충남 논산시 강경읍 C지구', '충남 논산시', 36.1662, 126.8779, 750, 700000,
        0, 1, 17, '사질토, 용수 미확보', '개선필요', 'idle', '2026-02-01T00:00:00+00:00', '2026-02-01T00:00:00+00:00'),
    -- Land already converted and operating a tomato smart farm (used by the
    -- sensor / wholesaler-match / price-forecast scenarios below).
    ('farmland-existing', 'user-landowner-existing', '충남 논산시 연무읍 D지구', '충남 논산시', 36.1074, 127.0512, 1200, 600000,
        1, 1, 15, '양토, 배수 양호', '최상', 'operating', '2025-12-01T00:00:00+00:00', '2026-03-01T00:00:00+00:00');

-- ---------------------------------------------------------------------------
-- Smart farm on the existing land, growing tomatoes for 김농부
-- ---------------------------------------------------------------------------

INSERT INTO smart_farms (id, farmland_id, farmer_user_id, farm_type, operation_start_date, created_at) VALUES
    ('smart-farm-tomato', 'farmland-existing', 'user-farmer-kim', '시설하우스 수경재배', '2026-03-01', '2026-03-01T00:00:00+00:00');

-- Environment control example (SPEC 5.5): before/after readings per metric.
INSERT INTO sensor_readings (id, smart_farm_id, metric, value, unit, measured_at) VALUES
    ('reading-temp-before', 'smart-farm-tomato', 'temperature', 29.4, 'celsius', '2026-08-05T05:00:00+00:00'),
    ('reading-temp-after', 'smart-farm-tomato', 'temperature', 26.5, 'celsius', '2026-08-05T05:20:00+00:00'),
    ('reading-humidity-stable', 'smart-farm-tomato', 'humidity', 68, 'percent', '2026-08-05T05:00:00+00:00'),
    ('reading-soil-before', 'smart-farm-tomato', 'soil_moisture', 28, 'percent', '2026-08-05T05:00:00+00:00'),
    ('reading-soil-after', 'smart-farm-tomato', 'soil_moisture', 41, 'percent', '2026-08-05T05:15:00+00:00'),
    -- 16400 lux = 82% of the 20000 lux floor; 20200 lux = 101% after lighting kicks in.
    ('reading-light-before', 'smart-farm-tomato', 'light', 16400, 'lux', '2026-08-05T05:00:00+00:00'),
    ('reading-light-after', 'smart-farm-tomato', 'light', 20200, 'lux', '2026-08-05T05:10:00+00:00');

-- ---------------------------------------------------------------------------
-- Shipment plans
-- ---------------------------------------------------------------------------

-- SPEC 5.1 / 5.2: the 1000kg tomato lot used for price-forecast and
-- wholesaler-comparison scenarios.
INSERT INTO shipment_plans (
    id, farmer_user_id, smart_farm_id, crop_id, region, expected_yield_kg,
    planned_shipment_date, grade, status, created_at, updated_at
) VALUES
    ('shipment-tomato-main', 'user-farmer-kim', 'smart-farm-tomato', 'crop-tomato', '충남 논산시',
        1000, '2026-08-10', '상품', 'planned', '2026-07-20T00:00:00+00:00', '2026-07-20T00:00:00+00:00');

-- SPEC 5.3: a separate 1700kg tomato lot split across four grades, one per
-- recommended retailer type.
INSERT INTO shipment_plans (
    id, farmer_user_id, smart_farm_id, crop_id, region, expected_yield_kg,
    planned_shipment_date, grade, status, created_at, updated_at
) VALUES
    ('shipment-tomato-premium', 'user-farmer-kim', 'smart-farm-tomato', 'crop-tomato', '충남 논산시',
        300, '2026-08-20', '특상품', 'planned', '2026-08-01T00:00:00+00:00', '2026-08-01T00:00:00+00:00'),
    ('shipment-tomato-standard', 'user-farmer-kim', 'smart-farm-tomato', 'crop-tomato', '충남 논산시',
        700, '2026-08-20', '상품', 'planned', '2026-08-01T00:00:00+00:00', '2026-08-01T00:00:00+00:00'),
    ('shipment-tomato-offgrade', 'user-farmer-kim', 'smart-farm-tomato', 'crop-tomato', '충남 논산시',
        500, '2026-08-20', '규격외', 'planned', '2026-08-01T00:00:00+00:00', '2026-08-01T00:00:00+00:00'),
    ('shipment-tomato-urgent', 'user-farmer-kim', 'smart-farm-tomato', 'crop-tomato', '충남 논산시',
        200, '2026-08-20', '판매기한임박', 'planned', '2026-08-01T00:00:00+00:00', '2026-08-01T00:00:00+00:00');

-- SPEC 5.4: three onion growers whose combined planned shipments (50t + 40t +
-- 30t = 120t) form the region's oversupply.
INSERT INTO shipment_plans (
    id, farmer_user_id, smart_farm_id, crop_id, region, expected_yield_kg,
    planned_shipment_date, grade, status, created_at, updated_at
) VALUES
    ('shipment-onion-kim', 'user-farmer-kim', NULL, 'crop-onion', '충남 논산시',
        50000, '2026-09-15', '상품', 'planned', '2026-08-15T00:00:00+00:00', '2026-08-15T00:00:00+00:00'),
    ('shipment-onion-park', 'user-farmer-park', NULL, 'crop-onion', '충남 논산시',
        40000, '2026-09-15', '상품', 'planned', '2026-08-15T00:00:00+00:00', '2026-08-15T00:00:00+00:00'),
    ('shipment-onion-choi', 'user-farmer-choi', NULL, 'crop-onion', '충남 논산시',
        30000, '2026-09-15', '상품', 'planned', '2026-08-15T00:00:00+00:00', '2026-08-15T00:00:00+00:00');

-- ---------------------------------------------------------------------------
-- Market price history -- SPEC 5.1 tomato forecast dates plus a short trailing
-- history so trend queries have something to work with.
-- ---------------------------------------------------------------------------

INSERT INTO market_prices (id, crop_id, price_date, region, wholesale_price_krw_per_kg, transaction_volume_kg, shipment_volume_kg) VALUES
    ('price-tomato-0801', 'crop-tomato', '2026-08-01', '충남 논산시', 2400, 42000, 41000),
    ('price-tomato-0805', 'crop-tomato', '2026-08-05', '충남 논산시', 2430, 43500, 42800),
    ('price-tomato-0808', 'crop-tomato', '2026-08-08', '충남 논산시', 2450, 44000, 43200),
    ('price-tomato-0810', 'crop-tomato', '2026-08-10', '충남 논산시', 2580, 41000, 39800),
    ('price-tomato-0817', 'crop-tomato', '2026-08-17', '충남 논산시', 2320, 47000, 46500),
    ('price-onion-0901', 'crop-onion', '2026-09-01', '충남 논산시', 980, 118000, 115000),
    ('price-onion-0908', 'crop-onion', '2026-09-08', '충남 논산시', 950, 121000, 119500),
    ('price-strawberry-0801', 'crop-strawberry', '2026-08-01', '충남 논산시', 9800, 8200, 8000);

-- ---------------------------------------------------------------------------
-- Wholesalers and their tomato offers -- SPEC 5.2 comparison table
-- ---------------------------------------------------------------------------

INSERT INTO wholesalers (id, user_id, name, region, location, created_at) VALUES
    ('wholesaler-a', 'user-wholesaler-a', '도매처 A', '충남 논산시', '논산농산물도매시장', '2026-01-01T00:00:00+00:00'),
    ('wholesaler-b', 'user-wholesaler-b', '도매처 B', '충남 논산시', '논산농산물도매시장', '2026-01-01T00:00:00+00:00'),
    ('wholesaler-c', 'user-wholesaler-c', '도매처 C', '충남 부여군', '부여농산물도매시장', '2026-01-01T00:00:00+00:00');

-- transport_cost_krw and commission_rate are the pre-computed figures from
-- SPEC 5.2's table; see the schema comment on this table for why they are
-- stored directly rather than derived purely from distance_km.
INSERT INTO wholesaler_crop_offers (
    id, wholesaler_id, crop_id, purchase_unit_price_krw_per_kg, purchase_capacity_kg,
    distance_km, transport_cost_krw, commission_rate, created_at
) VALUES
    ('offer-tomato-a', 'wholesaler-a', 'crop-tomato', 2550, 1000, 22, 180000, 0.03, '2026-07-25T00:00:00+00:00'),
    ('offer-tomato-b', 'wholesaler-b', 'crop-tomato', 2580, 1000, 12, 80000, 0.03, '2026-07-25T00:00:00+00:00'),
    ('offer-tomato-c', 'wholesaler-c', 'crop-tomato', 2700, 800, 29, 210000, 0.03, '2026-07-25T00:00:00+00:00');

-- Onion inventory already held by wholesaler A (SPEC 5.4: "도매처 기존 재고량 8톤").
INSERT INTO wholesaler_inventories (id, wholesaler_id, crop_id, quantity_kg, as_of_date, created_at) VALUES
    ('inventory-onion-a', 'wholesaler-a', 'crop-onion', 8000, '2026-09-01', '2026-09-01T00:00:00+00:00');

-- ---------------------------------------------------------------------------
-- Retailers and demand -- SPEC 5.3 grade matching, SPEC 5.4 onion demand
-- ---------------------------------------------------------------------------

INSERT INTO retailers (id, user_id, name, retailer_type, region, location, delivery_terms, created_at) VALUES
    ('retailer-mart', 'user-retailer-mart', '한마음 대형마트', '대형마트', '충남 논산시', '논산점', '규격 균일, 정기 납품', '2026-01-01T00:00:00+00:00'),
    ('retailer-school', 'user-retailer-school', '논산 학교급식지원센터', '학교급식', '충남 논산시', '논산시청 인근', '위생 등급 A, 소포장', '2026-01-01T00:00:00+00:00'),
    ('retailer-factory', 'user-retailer-factory', '들녘소스 가공업체', '가공업체', '충남 논산시', '연무읍 산업단지', '규격 무관, 대량 매입', '2026-01-01T00:00:00+00:00'),
    ('retailer-restaurant', 'user-retailer-restaurant', '논산 지역 음식점 조합', '지역음식점', '충남 논산시', '논산시 원도심', '신속 배송, 소량 다빈도', '2026-01-01T00:00:00+00:00');

INSERT INTO retailer_crop_demands (id, retailer_id, crop_id, grade, demand_quantity_kg, as_of_date, created_at) VALUES
    ('demand-tomato-mart', 'retailer-mart', 'crop-tomato', '특상품', 300, '2026-08-15', '2026-08-01T00:00:00+00:00'),
    ('demand-tomato-school', 'retailer-school', 'crop-tomato', '상품', 700, '2026-08-15', '2026-08-01T00:00:00+00:00'),
    ('demand-tomato-factory', 'retailer-factory', 'crop-tomato', '규격외', 500, '2026-08-15', '2026-08-01T00:00:00+00:00'),
    ('demand-tomato-restaurant', 'retailer-restaurant', 'crop-tomato', '판매기한임박', 200, '2026-08-15', '2026-08-01T00:00:00+00:00'),
    -- Onion demand from SPEC 5.4: 60t (mart) + 40t (school) = 100t total.
    ('demand-onion-mart', 'retailer-mart', 'crop-onion', NULL, 60000, '2026-09-15', '2026-09-01T00:00:00+00:00'),
    ('demand-onion-school', 'retailer-school', 'crop-onion', NULL, 40000, '2026-09-15', '2026-09-01T00:00:00+00:00');

-- ---------------------------------------------------------------------------
-- AI recommendations
-- ---------------------------------------------------------------------------

-- SPEC 5.1: price forecast for three candidate shipment dates on the 1000kg
-- tomato lot. score = expected sale amount in KRW (price * 1000kg).
INSERT INTO ai_recommendations (
    id, recommendation_type, subject_type, subject_id, target_type, target_id,
    score, rank, rationale, metadata, created_at
) VALUES
    ('rec-price-0808', 'price_forecast', 'shipment_plan', 'shipment-tomato-main', 'shipment_date', '2026-08-08',
        2450000, 2, '공급량 보통 예상. 즉시 출하 가능한 기준 시나리오.',
        '{"price_krw_per_kg": 2450, "change_percent_vs_base": 0.0, "market_outlook": "공급량 보통", "guidance": "즉시 출하 가능"}',
        '2026-07-28T00:00:00+00:00'),
    ('rec-price-0810', 'price_forecast', 'shipment_plan', 'shipment-tomato-main', 'shipment_date', '2026-08-10',
        2580000, 1, '공급량 감소 예상으로 가격이 약 5.3% 상승할 전망. 출하 유지를 권장.',
        '{"price_krw_per_kg": 2580, "change_percent_vs_base": 5.3, "market_outlook": "공급량 감소 예상", "guidance": "출하 유지 권장"}',
        '2026-07-28T00:00:00+00:00'),
    ('rec-price-0817', 'price_forecast', 'shipment_plan', 'shipment-tomato-main', 'shipment_date', '2026-08-17',
        2320000, 3, '공급량 증가 예상으로 가격이 약 5.3% 하락할 전망. 조기 출하 검토를 권장.',
        '{"price_krw_per_kg": 2320, "change_percent_vs_base": -5.3, "market_outlook": "공급량 증가 예상", "guidance": "조기 출하 검토"}',
        '2026-07-28T00:00:00+00:00');

-- SPEC 5.2: wholesaler comparison for the same 1000kg lot. score = net profit
-- in KRW as printed in the spec table (판매금액 - 운송비 - 수수료, rounded per source).
INSERT INTO ai_recommendations (
    id, recommendation_type, subject_type, subject_id, target_type, target_id,
    score, rank, rationale, metadata, created_at, outcome, decided_at
) VALUES
    ('rec-wholesaler-a', 'wholesaler_match', 'shipment_plan', 'shipment-tomato-main', 'wholesaler', 'wholesaler-a',
        2395000, 2, '매입단가는 세 곳 중 가장 낮지만 운송비가 높아 순수익은 2위.',
        '{"purchase_unit_price_krw_per_kg": 2550, "quantity_kg": 1000, "transport_cost_krw": 180000}',
        '2026-07-29T00:00:00+00:00', 'rejected', '2026-07-30T00:00:00+00:00'),
    ('rec-wholesaler-b', 'wholesaler_match', 'shipment_plan', 'shipment-tomato-main', 'wholesaler', 'wholesaler-b',
        2422600, 1, '매입단가가 높고 거리가 가까워 운송비가 가장 낮음. 순수익 1위로 추천.',
        '{"purchase_unit_price_krw_per_kg": 2580, "quantity_kg": 1000, "transport_cost_krw": 80000}',
        '2026-07-29T00:00:00+00:00', 'selected', '2026-07-30T00:00:00+00:00'),
    ('rec-wholesaler-c', 'wholesaler_match', 'shipment_plan', 'shipment-tomato-main', 'wholesaler', 'wholesaler-c',
        1885200, 3, '매입단가는 가장 높으나 구매 가능량이 800kg로 제한되고 운송비도 높아 순수익은 3위.',
        '{"purchase_unit_price_krw_per_kg": 2700, "quantity_kg": 800, "transport_cost_krw": 210000}',
        '2026-07-29T00:00:00+00:00', 'rejected', '2026-07-30T00:00:00+00:00');

-- SPEC 5.3: grade-based retailer matching, one recommendation per shipment lot.
INSERT INTO ai_recommendations (
    id, recommendation_type, subject_type, subject_id, target_type, target_id,
    score, rank, rationale, created_at
) VALUES
    ('rec-retailer-premium', 'retailer_match', 'shipment_plan', 'shipment-tomato-premium', 'retailer', 'retailer-mart',
        300, 1, '외관과 크기가 균일한 특상품으로 대형마트 진열 규격에 적합.', '2026-08-02T00:00:00+00:00'),
    ('rec-retailer-standard', 'retailer_match', 'shipment_plan', 'shipment-tomato-standard', 'retailer', 'retailer-school',
        700, 1, '대용량 안정 공급이 가능한 상품 등급으로 학교급식 납품에 적합.', '2026-08-02T00:00:00+00:00'),
    ('rec-retailer-offgrade', 'retailer_match', 'shipment_plan', 'shipment-tomato-offgrade', 'retailer', 'retailer-factory',
        500, 1, '품질은 정상이나 모양이 불규칙해 소스 가공업체의 원료로 적합.', '2026-08-02T00:00:00+00:00'),
    ('rec-retailer-urgent', 'retailer_match', 'shipment_plan', 'shipment-tomato-urgent', 'retailer', 'retailer-restaurant',
        200, 1, '판매기한이 임박해 신속한 소진이 가능한 지역 음식점에 우선 연결.', '2026-08-02T00:00:00+00:00');

-- SPEC 5.4: onion supply-risk alert for the region. score = excess supply in
-- kg (negative = oversupply). metadata carries the full breakdown table.
INSERT INTO ai_recommendations (
    id, recommendation_type, subject_type, subject_id, target_type, target_id,
    score, rationale, metadata, created_at
) VALUES
    ('rec-supply-risk-onion', 'supply_risk_alert', 'crop', 'crop-onion', 'region', '충남 논산시',
        -28000, '농가 출하 예정량과 도매처 재고를 합한 공급량이 판매처 구매 수요보다 28톤 많아 위험 단계로 판단.',
        '{"farmer_planned_kg": 120000, "wholesaler_inventory_kg": 8000, "total_supply_kg": 128000, ' ||
        '"retailer_demand_kg": 100000, "excess_supply_kg": 28000, "risk_level": "위험", ' ||
        '"mitigation_plan": [' ||
        '{"action": "식품가공업체 추가 연결", "quantity_kg": 12000}, ' ||
        '{"action": "학교급식 업체 추가 연결", "quantity_kg": 6000}, ' ||
        '{"action": "출하 시기 조정", "quantity_kg": 7000}, ' ||
        '{"action": "지역 공동판매 연계", "quantity_kg": 3000}]}',
        '2026-08-20T00:00:00+00:00');

-- SPEC 5.6: farmland recommendation for a strawberry farmer searching for
-- 700-1000 pyeong. Scores are an illustrative suitability score (0-100); the
-- spec itself only gives ranks, not numeric scores.
INSERT INTO ai_recommendations (
    id, recommendation_type, subject_type, subject_id, target_type, target_id,
    score, rank, rationale, created_at
) VALUES
    ('rec-farmland-a', 'farmland_match', 'user', 'user-farmer-lee', 'farmland', 'farmland-a',
        92, 1, '농업용수 확보, 냉장창고 접근 가능, 도매처 거리 24km로 종합 조건이 가장 우수.', '2026-02-10T00:00:00+00:00'),
    ('rec-farmland-b', 'farmland_match', 'user', 'user-farmer-lee', 'farmland', 'farmland-b',
        78, 2, '면적이 가장 넓고 임대료가 저렴하나 냉장창고 접근이 제한적이고 도매처 거리가 멀어 2위.', '2026-02-10T00:00:00+00:00'),
    ('rec-farmland-c', 'farmland_match', 'user', 'user-farmer-lee', 'farmland', 'farmland-c',
        65, 3, '도매처 거리는 가장 가까우나 농업용수가 미확보 상태로 시설 투자가 추가로 필요해 3위.', '2026-02-10T00:00:00+00:00');

-- ---------------------------------------------------------------------------
-- Transaction -- the farmer's actual choice, feeding back from rec-wholesaler-b.
-- ---------------------------------------------------------------------------

INSERT INTO transactions (
    id, shipment_plan_id, wholesaler_id, counterparty_type, recommendation_id,
    quantity_kg, unit_price_krw_per_kg, transport_cost_krw, commission_krw,
    net_profit_krw, status, requested_at, updated_at
) VALUES
    ('txn-tomato-main', 'shipment-tomato-main', 'wholesaler-b', 'wholesaler', 'rec-wholesaler-b',
        1000, 2580, 80000, 77400, 2422600, 'completed', '2026-07-30T00:00:00+00:00', '2026-08-10T00:00:00+00:00');
