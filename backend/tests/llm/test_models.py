"""Tests for LLM structured output / input models."""

from app.llm.models import (
    BuyerMatch,
    BuyerRecommendation,
    ChatAssistantResult,
    FarmlandOption,
    FarmlandOptionExplanation,
    FarmlandRecommendation,
    FarmlandRequest,
    PriceForecastExplanation,
    ProduceLot,
    ResponseOption,
    ResponsePlanItem,
    ShipmentTimingAdvice,
    ShippingDateOption,
    SupplyRiskAlert,
    SupplyRiskInput,
    ToolCallOutcome,
    WholesalerOption,
    WholesalerOptionExplanation,
    WholesalerRecommendation,
)


class TestPriceForecastExplanation:
    def test_round_trip(self):
        resp = PriceForecastExplanation(
            crop_name="토마토",
            summary="요약",
            recommended_date="2025-08-10",
            recommendation_reason="가격이 가장 높습니다.",
            options=[
                ShipmentTimingAdvice(
                    date="2025-08-08", explanation="기준일입니다.", system_guidance="즉시 출하 가능"
                ),
                ShipmentTimingAdvice(
                    date="2025-08-10", explanation="상승 예상입니다.", system_guidance="출하 유지 권장"
                ),
            ],
        )
        parsed = PriceForecastExplanation.model_validate_json(resp.model_dump_json())
        assert parsed == resp

    def test_shipping_date_option_input(self):
        opt = ShippingDateOption(
            date="2025-08-17",
            expected_wholesale_price_per_kg=2320,
            expected_revenue=2_320_000,
            price_change_percent=-5.3,
            market_supply_condition="공급량 증가 예상",
        )
        assert opt.price_change_percent == -5.3


class TestWholesalerRecommendation:
    def test_round_trip(self):
        resp = WholesalerRecommendation(
            crop_name="토마토",
            recommended_wholesaler="B",
            recommendation_reason="순수익이 가장 높습니다.",
            options=[
                WholesalerOptionExplanation(name="A", rank=2, explanation="2위입니다."),
                WholesalerOptionExplanation(name="B", rank=1, explanation="1위입니다."),
            ],
        )
        parsed = WholesalerRecommendation.model_validate_json(resp.model_dump_json())
        assert parsed == resp

    def test_wholesaler_option_input(self):
        opt = WholesalerOption(
            name="B",
            purchase_price_per_kg=2580,
            purchase_quantity_kg=1000,
            transport_cost=80_000,
            net_profit=2_422_600,
            rank=1,
        )
        assert opt.rank == 1


class TestBuyerRecommendation:
    def test_buyer_type_literal(self):
        resp = BuyerRecommendation(
            matches=[
                BuyerMatch(lot_id="lot-1", recommended_buyer_type="소매점", reason="특상품입니다."),
                BuyerMatch(lot_id="lot-2", recommended_buyer_type="지역음식점", reason="임박 물량입니다."),
            ]
        )
        assert resp.matches[0].recommended_buyer_type == "소매점"

    def test_produce_lot_input(self):
        lot = ProduceLot(lot_id="lot-3", grade="규격 외", quantity_kg=500, condition_note="모양 불규칙")
        assert lot.quantity_kg == 500


class TestSupplyRiskAlert:
    def test_round_trip(self):
        resp = SupplyRiskAlert(
            region="충남",
            crop_name="양파",
            risk_level="위험",
            alert_message="공급 과잉이 예상됩니다.",
            situation_explanation="공급량이 수요보다 많습니다.",
            response_plan=[
                ResponsePlanItem(channel="식품가공업체 추가 연결", rationale="가공 수요를 흡수합니다."),
            ],
        )
        parsed = SupplyRiskAlert.model_validate_json(resp.model_dump_json())
        assert parsed == resp

    def test_supply_risk_input(self):
        risk_input = SupplyRiskInput(
            region="충남",
            crop_name="양파",
            farm_planned_shipment_ton=120,
            wholesaler_existing_stock_ton=8,
            total_supply_ton=128,
            buyer_demand_ton=100,
            excess_supply_ton=28,
            risk_level="위험",
            response_options=[ResponseOption(channel="출하 시기 조정", processed_volume_ton=7)],
        )
        assert risk_input.excess_supply_ton == 28


class TestFarmlandRecommendation:
    def test_round_trip(self):
        resp = FarmlandRecommendation(
            recommended_farmland="A",
            recommendation_reason="조건에 가장 잘 맞습니다.",
            options=[FarmlandOptionExplanation(name="A", rank=1, explanation="1위입니다.")],
        )
        parsed = FarmlandRecommendation.model_validate_json(resp.model_dump_json())
        assert parsed == resp

    def test_farmland_option_and_request_input(self):
        request = FarmlandRequest(desired_crop="딸기", desired_area_pyeong=900, budget_monthly_rent=650_000)
        option = FarmlandOption(
            name="A",
            area_pyeong=900,
            monthly_rent=650_000,
            water_access=True,
            cold_storage_access="가능",
            distance_to_wholesaler_km=24,
            rank=1,
        )
        assert request.desired_area_pyeong == option.area_pyeong


class TestChatAssistantResult:
    def test_message_only(self):
        result = ChatAssistantResult(message="안녕하세요")
        assert result.tool_calls == []

    def test_with_tool_call_outcome(self):
        outcome = ToolCallOutcome(
            name="create_trade_request",
            arguments={"crop_name": "토마토", "quantity_kg": 500},
            result={"request_id": "abc"},
        )
        result = ChatAssistantResult(message="거래 요청을 생성했습니다.", tool_calls=[outcome])
        assert result.tool_calls[0].error is None
        assert result.tool_calls[0].result["request_id"] == "abc"

    def test_tool_call_outcome_with_error(self):
        outcome = ToolCallOutcome(name="list_trade_requests", arguments={}, error="not found")
        assert outcome.result is None
        assert outcome.error == "not found"
