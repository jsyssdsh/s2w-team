"""Tests for the mock LLM provider (LLM_MOCK=true path)."""

from app.llm.mock import (
    mock_buyer_recommendation,
    mock_chat,
    mock_farmland_recommendation,
    mock_price_forecast,
    mock_supply_risk_alert,
    mock_wholesaler_recommendation,
)
from app.llm.models import (
    FarmlandOption,
    FarmlandRequest,
    ProduceLot,
    ResponseOption,
    ShippingDateOption,
    SupplyRiskInput,
    WholesalerOption,
)


class TestMockPriceForecast:
    def test_guidance_matches_price_direction(self):
        options = [
            ShippingDateOption(
                date="2025-08-08",
                expected_wholesale_price_per_kg=2450,
                expected_revenue=2_450_000,
                price_change_percent=0,
                market_supply_condition="공급량 보통",
            ),
            ShippingDateOption(
                date="2025-08-10",
                expected_wholesale_price_per_kg=2580,
                expected_revenue=2_580_000,
                price_change_percent=5.3,
                market_supply_condition="공급량 감소 예상",
            ),
            ShippingDateOption(
                date="2025-08-17",
                expected_wholesale_price_per_kg=2320,
                expected_revenue=2_320_000,
                price_change_percent=-5.3,
                market_supply_condition="공급량 증가 예상",
            ),
        ]
        result = mock_price_forecast("토마토", options)
        guidance_by_date = {o.date: o.system_guidance for o in result.options}
        assert guidance_by_date["2025-08-08"] == "즉시 출하 가능"
        assert guidance_by_date["2025-08-10"] == "출하 유지 권장"
        assert guidance_by_date["2025-08-17"] == "조기 출하 검토"
        assert result.recommended_date == "2025-08-10"  # highest expected_revenue


class TestMockWholesalerRecommendation:
    def test_recommends_rank_one(self):
        options = [
            WholesalerOption(
                name="A", purchase_price_per_kg=2550, purchase_quantity_kg=1000,
                transport_cost=180_000, net_profit=2_395_000, rank=2,
            ),
            WholesalerOption(
                name="B", purchase_price_per_kg=2580, purchase_quantity_kg=1000,
                transport_cost=80_000, net_profit=2_422_600, rank=1,
            ),
            WholesalerOption(
                name="C", purchase_price_per_kg=2700, purchase_quantity_kg=800,
                transport_cost=210_000, net_profit=1_885_200, rank=3,
            ),
        ]
        result = mock_wholesaler_recommendation("토마토", options)
        assert result.recommended_wholesaler == "B"
        assert "2,422,600" in result.recommendation_reason


class TestMockBuyerRecommendation:
    def test_lot_type_mapping(self):
        lots = [
            ProduceLot(lot_id="l1", grade="특상품", quantity_kg=300, condition_note="외관과 크기가 균일함"),
            ProduceLot(lot_id="l2", grade="가정용", quantity_kg=700, condition_note="대용량 판매 가능"),
            ProduceLot(lot_id="l3", grade="규격 외", quantity_kg=500, condition_note="모양이 불규칙함"),
            ProduceLot(lot_id="l4", grade="정상 품질", quantity_kg=200, condition_note="판매기한 임박"),
        ]
        result = mock_buyer_recommendation(lots)
        by_id = {m.lot_id: m.recommended_buyer_type for m in result.matches}
        assert by_id["l1"] == "소매점"
        assert by_id["l2"] == "급식업체"
        assert by_id["l3"] == "가공업체"
        assert by_id["l4"] == "지역음식점"


class TestMockSupplyRiskAlert:
    def test_formats_precomputed_numbers(self):
        risk_input = SupplyRiskInput(
            region="충남",
            crop_name="양파",
            farm_planned_shipment_ton=120,
            wholesaler_existing_stock_ton=8,
            total_supply_ton=128,
            buyer_demand_ton=100,
            excess_supply_ton=28,
            risk_level="위험",
            response_options=[
                ResponseOption(channel="식품가공업체 추가 연결", processed_volume_ton=12),
                ResponseOption(channel="출하 시기 조정", processed_volume_ton=7),
            ],
        )
        result = mock_supply_risk_alert(risk_input)
        assert result.risk_level == "위험"
        assert "28.0톤" in result.alert_message
        assert len(result.response_plan) == 2
        assert result.response_plan[0].channel == "식품가공업체 추가 연결"


class TestMockFarmlandRecommendation:
    def test_recommends_rank_one(self):
        request = FarmlandRequest(desired_crop="딸기", desired_area_pyeong=900, budget_monthly_rent=650_000)
        options = [
            FarmlandOption(
                name="A", area_pyeong=900, monthly_rent=650_000, water_access=True,
                cold_storage_access="가능", distance_to_wholesaler_km=24, rank=1,
            ),
            FarmlandOption(
                name="B", area_pyeong=1000, monthly_rent=550_000, water_access=True,
                cold_storage_access="제한적", distance_to_wholesaler_km=38, rank=2,
            ),
        ]
        result = mock_farmland_recommendation(request, options)
        assert result.recommended_farmland == "A"


class TestMockChat:
    async def test_greeting_no_tools(self):
        result = await mock_chat("안녕하세요", None, {})
        assert "울퉁불퉁 농장 AI" in result.message
        assert result.tool_calls == []

    async def test_create_trade_request_calls_executor(self):
        calls = []

        async def create_trade_request(**kwargs):
            calls.append(kwargs)
            return {"request_id": "req-1", "status": "pending"}

        result = await mock_chat(
            "토마토 500kg B도매처에 거래 요청해줘", None, {"create_trade_request": create_trade_request}
        )
        assert calls == [{"crop_name": "토마토", "quantity_kg": 500.0, "counterparty_name": "B도매처"}]
        assert result.tool_calls[0].result == {"request_id": "req-1", "status": "pending"}
        assert "B도매처" in result.message

    async def test_create_trade_request_missing_executor(self):
        result = await mock_chat("토마토 500kg B도매처에 거래 요청해줘", None, {})
        assert result.tool_calls[0].error is not None
        assert "만들지 못했습니다" in result.message

    async def test_list_trade_requests_calls_executor(self):
        async def list_trade_requests(**kwargs):
            return {"requests": [{"request_id": "req-1"}, {"request_id": "req-2"}]}

        result = await mock_chat(
            "거래 요청 목록 보여줘", None, {"list_trade_requests": list_trade_requests}
        )
        assert "2건" in result.message
