"""Tests for the S2W database layer, against a fresh temp SQLite DB per test."""

import json

import pytest

from app.db import (
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
    get_crop_by_name,
    get_crop_optimal_ranges,
    get_farmland,
    get_latest_sensor_readings,
    get_price_history,
    get_recommendation,
    get_recommendations_for_subject,
    get_retailer_candidates_for_grade,
    get_sensor_readings_range,
    get_shipment_plans_by_farmer,
    get_smart_farm_by_farmland,
    get_supply_demand_balance,
    get_total_retailer_demand,
    get_total_wholesaler_inventory,
    get_wholesaler_candidates,
    init_db,
    insert_chat_message,
    insert_market_price,
    insert_sensor_reading,
    list_shipment_plans,
    list_smart_farms,
    list_smart_farms_by_farmer,
    record_recommendation_outcome,
    search_farmlands,
    set_db_path,
    update_farmland_status,
    update_shipment_plan_status,
    update_transaction_status,
    upsert_crop_optimal_range,
    upsert_wholesaler_inventory,
)


@pytest.fixture(autouse=True)
async def temp_db(tmp_path):
    """Use a fresh temporary database for each test -- never a developer's real db file."""
    db_path = str(tmp_path / "test.db")
    set_db_path(db_path)
    await init_db()
    yield db_path


class TestInitialization:
    async def test_init_creates_no_rows(self):
        # init_db only creates the schema; seeding is a separate, opt-in step.
        farmlands = await search_farmlands()
        assert farmlands == []

    async def test_init_is_idempotent(self):
        await init_db()
        await init_db()
        farmlands = await search_farmlands()
        assert farmlands == []


class TestUsersAndCrops:
    async def test_create_and_get_crop_by_name(self):
        await create_crop("토마토")
        crop = await get_crop_by_name("토마토")
        assert crop is not None
        assert crop["unit"] == "kg"

    async def test_crop_optimal_range_roundtrip(self):
        crop = await create_crop("토마토")
        await upsert_crop_optimal_range(crop["id"], "temperature", 22, 27, "celsius")
        ranges = await get_crop_optimal_ranges(crop["id"])
        assert len(ranges) == 1
        assert ranges[0]["min_value"] == 22
        assert ranges[0]["max_value"] == 27

    async def test_crop_optimal_range_upsert_replaces(self):
        crop = await create_crop("토마토")
        await upsert_crop_optimal_range(crop["id"], "temperature", 22, 27, "celsius")
        await upsert_crop_optimal_range(crop["id"], "temperature", 20, 28, "celsius")
        ranges = await get_crop_optimal_ranges(crop["id"])
        assert len(ranges) == 1
        assert ranges[0]["min_value"] == 20
        assert ranges[0]["max_value"] == 28


class TestFarmlandSearch:
    async def _seed_three_farmlands(self):
        owner = await create_user("landowner", "지주")
        await create_farmland(
            owner["id"], "A지구", 900, 650000, True, True, "최상",
            region="충남", distance_to_wholesaler_km=24,
        )
        await create_farmland(
            owner["id"], "B지구", 1000, 550000, True, False, "양호",
            region="충남", distance_to_wholesaler_km=38,
        )
        await create_farmland(
            owner["id"], "C지구", 750, 700000, False, True, "개선필요",
            region="충남", distance_to_wholesaler_km=17,
        )

    async def test_search_by_area_range(self):
        await self._seed_three_farmlands()
        results = await search_farmlands(min_area_pyeong=800, max_area_pyeong=950)
        assert len(results) == 1
        assert results[0]["address"] == "A지구"

    async def test_search_by_rent_ceiling(self):
        await self._seed_three_farmlands()
        results = await search_farmlands(max_monthly_rent_krw=600000)
        addresses = {r["address"] for r in results}
        assert addresses == {"B지구"}

    async def test_search_requiring_water_access(self):
        await self._seed_three_farmlands()
        results = await search_farmlands(require_water_access=True)
        addresses = {r["address"] for r in results}
        assert addresses == {"A지구", "B지구"}

    async def test_search_no_filters_returns_all(self):
        await self._seed_three_farmlands()
        results = await search_farmlands()
        assert len(results) == 3

    async def test_update_farmland_status(self):
        owner = await create_user("landowner", "지주")
        farmland = await create_farmland(
            owner["id"], "A지구", 900, 650000, True, True, "최상"
        )
        assert farmland["status"] == "idle"
        updated = await update_farmland_status(farmland["id"], "matched")
        assert updated["status"] == "matched"
        fetched = await get_farmland(farmland["id"])
        assert fetched["status"] == "matched"


class TestSmartFarmsAndSensors:
    async def test_sensor_reading_roundtrip(self):
        owner = await create_user("landowner", "지주")
        farmer = await create_user("farmer", "농부")
        farmland = await create_farmland(owner["id"], "D지구", 1200, 600000, True, True, "최상")
        farm = await create_smart_farm(
            farmland["id"], farmer["id"], "시설하우스", "2026-03-01"
        )

        await insert_sensor_reading(
            farm["id"], "temperature", 29.4, "celsius", "2026-08-05T05:00:00+00:00"
        )
        await insert_sensor_reading(
            farm["id"], "temperature", 26.5, "celsius", "2026-08-05T05:20:00+00:00"
        )

        latest = await get_latest_sensor_readings(farm["id"])
        assert latest["temperature"]["value"] == 26.5

        series = await get_sensor_readings_range(
            farm["id"], "temperature", "2026-08-05T00:00:00+00:00", "2026-08-05T23:59:59+00:00"
        )
        assert [r["value"] for r in series] == [29.4, 26.5]

    async def test_list_smart_farms_by_farmer(self):
        owner = await create_user("landowner", "지주")
        farmer = await create_user("farmer", "농부")
        farmland = await create_farmland(owner["id"], "D지구", 1200, 600000, True, True, "최상")
        await create_smart_farm(farmland["id"], farmer["id"], "시설하우스", "2026-03-01")

        farms = await list_smart_farms_by_farmer(farmer["id"])
        assert len(farms) == 1

    async def test_list_smart_farms_returns_every_farm(self):
        owner = await create_user("landowner", "지주")
        farmer1 = await create_user("farmer", "농부1")
        farmer2 = await create_user("farmer", "농부2")
        farmland1 = await create_farmland(owner["id"], "D지구", 1200, 600000, True, True, "최상")
        farmland2 = await create_farmland(owner["id"], "E지구", 900, 500000, True, True, "양호")
        await create_smart_farm(farmland1["id"], farmer1["id"], "시설하우스", "2026-03-01")
        await create_smart_farm(farmland2["id"], farmer2["id"], "노지형", "2026-04-01")

        farms = await list_smart_farms()
        assert len(farms) == 2

    async def test_get_smart_farm_by_farmland(self):
        owner = await create_user("landowner", "지주")
        farmer = await create_user("farmer", "농부")
        farmland = await create_farmland(owner["id"], "D지구", 1200, 600000, True, True, "최상")
        farm = await create_smart_farm(farmland["id"], farmer["id"], "시설하우스", "2026-03-01")

        found = await get_smart_farm_by_farmland(farmland["id"])
        assert found is not None
        assert found["id"] == farm["id"]

    async def test_get_smart_farm_by_farmland_returns_none_when_unmatched(self):
        owner = await create_user("landowner", "지주")
        farmland = await create_farmland(owner["id"], "D지구", 1200, 600000, True, True, "최상")

        assert await get_smart_farm_by_farmland(farmland["id"]) is None


class TestShipmentPlans:
    async def test_get_shipment_plans_by_farmer_filters_by_status(self):
        farmer = await create_user("farmer", "농부")
        crop = await create_crop("토마토")
        await create_shipment_plan(farmer["id"], crop["id"], 1000, "2026-08-10", "상품")
        plan2 = await create_shipment_plan(farmer["id"], crop["id"], 500, "2026-08-20", "특상품")
        await update_shipment_plan_status(plan2["id"], "shipped")

        planned = await get_shipment_plans_by_farmer(farmer["id"], status="planned")
        shipped = await get_shipment_plans_by_farmer(farmer["id"], status="shipped")
        assert len(planned) == 1
        assert len(shipped) == 1

    async def test_get_shipment_plans_by_farmer_no_filter(self):
        farmer = await create_user("farmer", "농부")
        crop = await create_crop("토마토")
        await create_shipment_plan(farmer["id"], crop["id"], 1000, "2026-08-10", "상품")
        await create_shipment_plan(farmer["id"], crop["id"], 500, "2026-08-20", "특상품")
        plans = await get_shipment_plans_by_farmer(farmer["id"])
        assert len(plans) == 2

    async def test_list_shipment_plans_across_farmers_by_crop(self):
        """Backs the wholesaler dashboard's cross-farmer 'AI 추천 농가 리스트' (SPEC 4.3)."""
        farmer1 = await create_user("farmer", "농부1")
        farmer2 = await create_user("farmer", "농부2")
        tomato = await create_crop("토마토")
        onion = await create_crop("양파")
        await create_shipment_plan(
            farmer1["id"], tomato["id"], 1000, "2026-08-10", "상품", region="충남"
        )
        await create_shipment_plan(
            farmer2["id"], tomato["id"], 500, "2026-08-12", "특상품", region="충남"
        )
        await create_shipment_plan(farmer1["id"], onion["id"], 50000, "2026-09-15", "상품")

        tomato_plans = await list_shipment_plans(crop_id=tomato["id"])
        assert len(tomato_plans) == 2
        assert {p["farmer_user_id"] for p in tomato_plans} == {farmer1["id"], farmer2["id"]}

    async def test_list_shipment_plans_no_filters_returns_all(self):
        farmer = await create_user("farmer", "농부")
        crop = await create_crop("토마토")
        await create_shipment_plan(farmer["id"], crop["id"], 1000, "2026-08-10", "상품")
        await create_shipment_plan(farmer["id"], crop["id"], 500, "2026-08-20", "특상품")

        assert len(await list_shipment_plans()) == 2


class TestMarketPrices:
    async def test_price_history_ordered_and_filterable(self):
        crop = await create_crop("토마토")
        await insert_market_price(crop["id"], "2026-08-17", 2320, region="충남")
        await insert_market_price(crop["id"], "2026-08-08", 2450, region="충남")
        await insert_market_price(crop["id"], "2026-08-10", 2580, region="충남")

        history = await get_price_history(crop["id"], region="충남")
        assert [h["price_date"] for h in history] == ["2026-08-08", "2026-08-10", "2026-08-17"]

        scoped = await get_price_history(
            crop["id"], region="충남", start_date="2026-08-09", end_date="2026-08-16"
        )
        assert len(scoped) == 1
        assert scoped[0]["price_date"] == "2026-08-10"


class TestWholesalerCandidates:
    async def test_wholesaler_comparison_matches_spec_example(self):
        """Reproduces SPEC 5.2's tomato wholesaler comparison table exactly."""
        crop = await create_crop("토마토")
        wa = await create_wholesaler("도매처 A")
        wb = await create_wholesaler("도매처 B")
        wc = await create_wholesaler("도매처 C")
        await create_wholesaler_crop_offer(wa["id"], crop["id"], 2550, 1000, 180000, 0.03)
        await create_wholesaler_crop_offer(wb["id"], crop["id"], 2580, 1000, 80000, 0.03)
        await create_wholesaler_crop_offer(wc["id"], crop["id"], 2700, 800, 210000, 0.03)

        candidates = await get_wholesaler_candidates(crop["id"])
        assert len(candidates) == 3

        # B has the best net profit despite not having the lowest transport cost
        # alone -- verify the raw inputs needed to derive SPEC's 순수익 ranking.
        net_profits = {
            c["wholesaler_name"]: round(
                c["purchase_unit_price_krw_per_kg"] * c["purchase_capacity_kg"]
                * (1 - c["commission_rate"])
                - c["transport_cost_krw"]
            )
            for c in candidates
        }
        ranked = sorted(net_profits, key=lambda name: net_profits[name], reverse=True)
        assert ranked[0] == "도매처 B"

    async def test_min_capacity_filter_excludes_smaller_offers(self):
        crop = await create_crop("토마토")
        wa = await create_wholesaler("도매처 A")
        wc = await create_wholesaler("도매처 C")
        await create_wholesaler_crop_offer(wa["id"], crop["id"], 2550, 1000, 180000, 0.03)
        await create_wholesaler_crop_offer(wc["id"], crop["id"], 2700, 800, 210000, 0.03)

        candidates = await get_wholesaler_candidates(crop["id"], min_capacity_kg=1000)
        assert len(candidates) == 1
        assert candidates[0]["wholesaler_name"] == "도매처 A"

    async def test_wholesaler_inventory_roundtrip_and_sum(self):
        crop = await create_crop("양파")
        wa = await create_wholesaler("도매처 A")
        wb = await create_wholesaler("도매처 B")
        await upsert_wholesaler_inventory(wa["id"], crop["id"], 5000, "2026-09-01")
        await upsert_wholesaler_inventory(wb["id"], crop["id"], 3000, "2026-09-01")

        total = await get_total_wholesaler_inventory(crop["id"])
        assert total == 8000

    async def test_wholesaler_inventory_upsert_replaces(self):
        crop = await create_crop("양파")
        wa = await create_wholesaler("도매처 A")
        await upsert_wholesaler_inventory(wa["id"], crop["id"], 5000, "2026-09-01")
        await upsert_wholesaler_inventory(wa["id"], crop["id"], 7000, "2026-09-08")

        total = await get_total_wholesaler_inventory(crop["id"])
        assert total == 7000


class TestRetailerMatching:
    async def test_grade_based_retailer_candidates_matches_spec_example(self):
        """Reproduces SPEC 5.3's grade-to-retailer-type matching."""
        crop = await create_crop("토마토")
        mart = await create_retailer("한마음마트", "대형마트")
        school = await create_retailer("급식센터", "학교급식")
        await create_retailer_crop_demand(mart["id"], crop["id"], 300, "2026-08-15", grade="특상품")
        await create_retailer_crop_demand(school["id"], crop["id"], 700, "2026-08-15", grade="상품")

        premium_candidates = await get_retailer_candidates_for_grade(crop["id"], "특상품")
        assert len(premium_candidates) == 1
        assert premium_candidates[0]["retailer_type"] == "대형마트"

    async def test_total_demand_ignores_other_crops(self):
        onion = await create_crop("양파")
        tomato = await create_crop("토마토")
        mart = await create_retailer("한마음마트", "대형마트")
        await create_retailer_crop_demand(mart["id"], onion["id"], 60000, "2026-09-15")
        await create_retailer_crop_demand(mart["id"], tomato["id"], 300, "2026-08-15")

        assert await get_total_retailer_demand(onion["id"]) == 60000


class TestSupplyDemandBalance:
    async def test_onion_supply_risk_matches_spec_example(self):
        """Reproduces SPEC 5.4's onion oversupply scenario: 128t supply vs 100t demand."""
        crop = await create_crop("양파")
        f1 = await create_user("farmer", "농부1")
        f2 = await create_user("farmer", "농부2")
        f3 = await create_user("farmer", "농부3")
        await create_shipment_plan(f1["id"], crop["id"], 50000, "2026-09-15", "상품", region="충남")
        await create_shipment_plan(f2["id"], crop["id"], 40000, "2026-09-15", "상품", region="충남")
        await create_shipment_plan(f3["id"], crop["id"], 30000, "2026-09-15", "상품", region="충남")

        wholesaler = await create_wholesaler("도매처 A", region="충남")
        await upsert_wholesaler_inventory(wholesaler["id"], crop["id"], 8000, "2026-09-01")

        mart = await create_retailer("한마음마트", "대형마트", region="충남")
        school = await create_retailer("급식센터", "학교급식", region="충남")
        await create_retailer_crop_demand(mart["id"], crop["id"], 60000, "2026-09-15")
        await create_retailer_crop_demand(school["id"], crop["id"], 40000, "2026-09-15")

        balance = await get_supply_demand_balance(crop["id"], region="충남")
        assert balance["farmer_planned_kg"] == 120000
        assert balance["wholesaler_inventory_kg"] == 8000
        assert balance["total_supply_kg"] == 128000
        assert balance["retailer_demand_kg"] == 100000
        assert balance["excess_supply_kg"] == 28000


class TestTransactionsAndRecommendations:
    async def test_transaction_status_transitions(self):
        farmer = await create_user("farmer", "농부")
        crop = await create_crop("토마토")
        plan = await create_shipment_plan(farmer["id"], crop["id"], 1000, "2026-08-10", "상품")
        wholesaler = await create_wholesaler("도매처 B")

        txn = await create_transaction(
            plan["id"], "wholesaler", 1000, 2580, wholesaler_id=wholesaler["id"]
        )
        assert txn["status"] == "requested"

        accepted = await update_transaction_status(txn["id"], "accepted")
        assert accepted["status"] == "accepted"

        completed = await update_transaction_status(txn["id"], "completed")
        assert completed["status"] == "completed"

    async def test_recommendation_roundtrip_with_metadata(self):
        farmer = await create_user("farmer", "농부")
        crop = await create_crop("토마토")
        plan = await create_shipment_plan(farmer["id"], crop["id"], 1000, "2026-08-10", "상품")
        wholesaler = await create_wholesaler("도매처 B")

        rec = await create_recommendation(
            "wholesaler_match", "shipment_plan", plan["id"], "wholesaler", wholesaler["id"],
            rationale="순수익 1위",
            score=2422600,
            rank=1,
            metadata={"purchase_unit_price_krw_per_kg": 2580},
        )
        fetched = await get_recommendation(rec["id"])
        assert fetched["metadata"] == {"purchase_unit_price_krw_per_kg": 2580}
        assert fetched["outcome"] is None

    async def test_recommendations_for_subject_ranked(self):
        farmer = await create_user("farmer", "농부")
        crop = await create_crop("토마토")
        plan = await create_shipment_plan(farmer["id"], crop["id"], 1000, "2026-08-10", "상품")
        wa = await create_wholesaler("도매처 A")
        wb = await create_wholesaler("도매처 B")

        await create_recommendation(
            "wholesaler_match", "shipment_plan", plan["id"], "wholesaler", wa["id"],
            rationale="2위", score=2395000, rank=2,
        )
        await create_recommendation(
            "wholesaler_match", "shipment_plan", plan["id"], "wholesaler", wb["id"],
            rationale="1위", score=2422600, rank=1,
        )

        recs = await get_recommendations_for_subject("shipment_plan", plan["id"])
        assert [r["rank"] for r in recs] == [1, 2]

    async def test_record_recommendation_outcome(self):
        farmer = await create_user("farmer", "농부")
        crop = await create_crop("토마토")
        plan = await create_shipment_plan(farmer["id"], crop["id"], 1000, "2026-08-10", "상품")
        wholesaler = await create_wholesaler("도매처 B")

        rec = await create_recommendation(
            "wholesaler_match", "shipment_plan", plan["id"], "wholesaler", wholesaler["id"],
            rationale="1위", score=2422600, rank=1,
        )
        assert rec["outcome"] is None

        updated = await record_recommendation_outcome(rec["id"], "selected")
        assert updated["outcome"] == "selected"
        assert updated["decided_at"] is not None


class TestChatMessages:
    async def test_insert_and_get_history_ordered_oldest_first(self):
        await insert_chat_message("user", "토마토 시세 알려줘", session_id="session-1")
        await insert_chat_message("assistant", "현재 kg당 2,580원입니다.", session_id="session-1")

        history = await get_chat_history(session_id="session-1")
        assert [m["role"] for m in history] == ["user", "assistant"]
        assert history[0]["content"] == "토마토 시세 알려줘"

    async def test_default_session_id_needs_no_argument(self):
        """Callers with no session/auth concept yet can omit session_id entirely."""
        await insert_chat_message("user", "안녕하세요")
        await insert_chat_message("assistant", "안녕하세요, 무엇을 도와드릴까요?")

        history = await get_chat_history()
        assert len(history) == 2
        assert history[0]["content"] == "안녕하세요"

    async def test_actions_roundtrip_on_assistant_message(self):
        actions = [{"name": "create_transaction", "arguments": {"quantity_kg": 1000}}]
        await insert_chat_message(
            "assistant", "도매처 B에 거래를 요청했습니다.", actions=actions, session_id="session-1"
        )

        history = await get_chat_history(session_id="session-1")
        assert history[0]["actions"] == actions

    async def test_actions_default_to_none(self):
        await insert_chat_message("user", "안녕하세요", session_id="session-1")

        history = await get_chat_history(session_id="session-1")
        assert history[0]["actions"] is None

    async def test_history_scoped_to_session(self):
        await insert_chat_message("user", "안녕하세요", session_id="session-1")
        await insert_chat_message("user", "다른 세션 메시지", session_id="session-2")

        history = await get_chat_history(session_id="session-1")
        assert len(history) == 1
        assert history[0]["content"] == "안녕하세요"

    async def test_tool_role_stores_json_content(self):
        outcome = {"name": "create_transaction", "arguments": {}, "result": {"status": "requested"}}
        await insert_chat_message(
            "tool", json.dumps(outcome, ensure_ascii=False), session_id="session-1"
        )

        history = await get_chat_history(session_id="session-1")
        assert json.loads(history[0]["content"]) == outcome

    async def test_history_limit_keeps_most_recent(self):
        for i in range(10):
            await insert_chat_message("user", f"메시지 {i}", session_id="session-1")

        history = await get_chat_history(limit=5, session_id="session-1")
        assert len(history) == 5
        assert history[0]["content"] == "메시지 5"
        assert history[-1]["content"] == "메시지 9"

    async def test_empty_history(self):
        history = await get_chat_history(session_id="session-does-not-exist")
        assert history == []
