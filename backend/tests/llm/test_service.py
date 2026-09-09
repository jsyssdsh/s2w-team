"""Tests for the LLM service layer. The real litellm.completion is always
mocked here -- no network/API calls are made."""

import json

import pytest

from app.llm import service as service_module
from app.llm.models import (
    FarmlandOption,
    FarmlandRequest,
    ProduceLot,
    ResponseOption,
    ShippingDateOption,
    SupplyRiskInput,
    WholesalerOption,
)
from app.llm.service import LlmServiceError, run_chat_assistant


class FakeFunction:
    def __init__(self, name, arguments):
        self.name = name
        self.arguments = arguments


class FakeToolCall:
    def __init__(self, call_id, name, arguments):
        self.id = call_id
        self.function = FakeFunction(name, arguments)


class FakeMessage:
    def __init__(self, content=None, tool_calls=None):
        self.content = content
        self.tool_calls = tool_calls


class FakeChoice:
    def __init__(self, message):
        self.message = message


class FakeResponse:
    def __init__(self, message):
        self.choices = [FakeChoice(message)]


def _content_response(payload: dict) -> FakeResponse:
    return FakeResponse(FakeMessage(content=json.dumps(payload, ensure_ascii=False)))


@pytest.fixture
def price_forecast_options():
    return [
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
    ]


class TestExplainPriceForecastMockMode:
    async def test_delegates_to_mock(self, monkeypatch, price_forecast_options):
        monkeypatch.setenv("LLM_MOCK", "true")
        result = await service_module.explain_price_forecast("토마토", price_forecast_options)
        assert result.crop_name == "토마토"
        assert result.recommended_date == "2025-08-10"


class TestExplainPriceForecastRealMode:
    async def test_parses_structured_response(self, monkeypatch, price_forecast_options):
        monkeypatch.delenv("LLM_MOCK", raising=False)
        payload = {
            "crop_name": "토마토",
            "summary": "요약",
            "recommended_date": "2025-08-10",
            "recommendation_reason": "가장 높은 판매금액입니다.",
            "options": [
                {"date": "2025-08-08", "explanation": "기준일", "system_guidance": "즉시 출하 가능"},
                {"date": "2025-08-10", "explanation": "상승 예상", "system_guidance": "출하 유지 권장"},
            ],
        }
        monkeypatch.setattr(
            service_module, "completion", lambda **kwargs: _content_response(payload)
        )
        result = await service_module.explain_price_forecast("토마토", price_forecast_options)
        assert result.recommended_date == "2025-08-10"
        assert result.options[0].system_guidance == "즉시 출하 가능"

    async def test_raises_after_retries_exhausted(self, monkeypatch, price_forecast_options):
        monkeypatch.delenv("LLM_MOCK", raising=False)

        def always_fails(**kwargs):
            raise RuntimeError("provider unavailable")

        monkeypatch.setattr(service_module, "completion", always_fails)
        with pytest.raises(LlmServiceError):
            await service_module.explain_price_forecast("토마토", price_forecast_options)


class TestRecommendWholesalerMockMode:
    async def test_delegates_to_mock(self, monkeypatch):
        monkeypatch.setenv("LLM_MOCK", "true")
        options = [
            WholesalerOption(
                name="A", purchase_price_per_kg=2550, purchase_quantity_kg=1000,
                transport_cost=180_000, net_profit=2_395_000, rank=2,
            ),
            WholesalerOption(
                name="B", purchase_price_per_kg=2580, purchase_quantity_kg=1000,
                transport_cost=80_000, net_profit=2_422_600, rank=1,
            ),
        ]
        result = await service_module.recommend_wholesaler("토마토", options)
        assert result.recommended_wholesaler == "B"


class TestRecommendBuyersMockMode:
    async def test_delegates_to_mock(self, monkeypatch):
        monkeypatch.setenv("LLM_MOCK", "true")
        lots = [ProduceLot(lot_id="l1", grade="특상품", quantity_kg=300, condition_note="균일함")]
        result = await service_module.recommend_buyers(lots)
        assert result.matches[0].recommended_buyer_type == "소매점"


class TestGenerateSupplyRiskAlertMockMode:
    async def test_delegates_to_mock(self, monkeypatch):
        monkeypatch.setenv("LLM_MOCK", "true")
        risk_input = SupplyRiskInput(
            region="충남", crop_name="양파", farm_planned_shipment_ton=120,
            wholesaler_existing_stock_ton=8, total_supply_ton=128, buyer_demand_ton=100,
            excess_supply_ton=28, risk_level="위험",
            response_options=[ResponseOption(channel="출하 시기 조정", processed_volume_ton=7)],
        )
        result = await service_module.generate_supply_risk_alert(risk_input)
        assert result.risk_level == "위험"


class TestRecommendFarmlandMockMode:
    async def test_delegates_to_mock(self, monkeypatch):
        monkeypatch.setenv("LLM_MOCK", "true")
        request = FarmlandRequest(desired_crop="딸기", desired_area_pyeong=900, budget_monthly_rent=650_000)
        options = [
            FarmlandOption(
                name="A", area_pyeong=900, monthly_rent=650_000, water_access=True,
                cold_storage_access="가능", distance_to_wholesaler_km=24, rank=1,
            ),
        ]
        result = await service_module.recommend_farmland(request, options)
        assert result.recommended_farmland == "A"


class TestRunChatAssistantMockMode:
    async def test_delegates_to_mock(self, monkeypatch):
        monkeypatch.setenv("LLM_MOCK", "true")
        result = await run_chat_assistant("안녕", [], {})
        assert "울퉁불퉁 농장 AI" in result.message


class TestRunChatAssistantRealMode:
    async def test_tool_call_then_final_message(self, monkeypatch):
        monkeypatch.delenv("LLM_MOCK", raising=False)

        tool_call = FakeToolCall(
            "call-1",
            "create_trade_request",
            json.dumps({"crop_name": "토마토", "quantity_kg": 500, "counterparty_name": "B도매처"}),
        )
        responses = [
            FakeResponse(FakeMessage(content=None, tool_calls=[tool_call])),
            FakeResponse(FakeMessage(content="B도매처에 거래 요청을 보냈습니다.", tool_calls=None)),
        ]

        def fake_completion(**kwargs):
            return responses.pop(0)

        monkeypatch.setattr(service_module, "completion", fake_completion)

        executed = []

        async def create_trade_request(**kwargs):
            executed.append(kwargs)
            return {"request_id": "req-1"}

        result = await run_chat_assistant(
            "토마토 500kg B도매처에 거래 요청해줘",
            [],
            {"create_trade_request": create_trade_request},
        )

        assert executed == [{"crop_name": "토마토", "quantity_kg": 500, "counterparty_name": "B도매처"}]
        assert result.message == "B도매처에 거래 요청을 보냈습니다."
        assert result.tool_calls[0].result == {"request_id": "req-1"}

    async def test_no_tool_call_returns_plain_message(self, monkeypatch):
        monkeypatch.delenv("LLM_MOCK", raising=False)
        monkeypatch.setattr(
            service_module,
            "completion",
            lambda **kwargs: FakeResponse(FakeMessage(content="시세가 안정적입니다.", tool_calls=None)),
        )
        result = await run_chat_assistant("요즘 토마토 시세 어때요?", [], {})
        assert result.message == "시세가 안정적입니다."
        assert result.tool_calls == []

    async def test_completion_failure_returns_fallback_message(self, monkeypatch):
        monkeypatch.delenv("LLM_MOCK", raising=False)

        def always_fails(**kwargs):
            raise RuntimeError("provider unavailable")

        monkeypatch.setattr(service_module, "completion", always_fails)
        result = await run_chat_assistant("안녕", [], {})
        assert "오류가 발생했습니다" in result.message
        assert result.tool_calls == []

    async def test_unknown_tool_reports_error_but_continues(self, monkeypatch):
        monkeypatch.delenv("LLM_MOCK", raising=False)

        tool_call = FakeToolCall("call-1", "no_such_tool", "{}")
        responses = [
            FakeResponse(FakeMessage(content=None, tool_calls=[tool_call])),
            FakeResponse(FakeMessage(content="처리했습니다.", tool_calls=None)),
        ]
        monkeypatch.setattr(service_module, "completion", lambda **kwargs: responses.pop(0))

        result = await run_chat_assistant("이상한 요청", [], {})
        assert result.tool_calls[0].error is not None
        assert result.message == "처리했습니다."
