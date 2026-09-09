"""Pydantic models for the LLM layer.

Two kinds of models live here:

- "Input" models carry numbers that are already computed by deterministic
  backend code (net profit, rankings, supply/demand totals, distances, ...).
  The LLM never invents or recomputes these numbers.
- "Output" models are what the LLM produces via structured output: natural
  language explanations and categorical recommendations, keyed back to the
  input items by name/date/id so the UI can merge them with the precomputed
  numbers. Output models intentionally do NOT repeat raw numeric fields —
  that keeps the LLM from silently altering a number while paraphrasing it.
"""

from typing import Any, Literal

from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# 5.1 시세 예측 근거 설명 및 출하 시기 제안
# ---------------------------------------------------------------------------

SystemGuidance = Literal["즉시 출하 가능", "출하 유지 권장", "조기 출하 검토"]


class ShippingDateOption(BaseModel):
    """One candidate shipping date with numbers already computed by backend."""

    date: str
    expected_wholesale_price_per_kg: float
    expected_revenue: float
    price_change_percent: float  # vs. current/baseline price, signed
    market_supply_condition: str  # e.g. "공급량 감소 예상"


class ShipmentTimingAdvice(BaseModel):
    date: str
    explanation: str
    system_guidance: SystemGuidance


class PriceForecastExplanation(BaseModel):
    crop_name: str
    summary: str
    recommended_date: str
    recommendation_reason: str
    options: list[ShipmentTimingAdvice]


# ---------------------------------------------------------------------------
# 5.2 농가 맞춤형 도매처 추천
# ---------------------------------------------------------------------------


class WholesalerOption(BaseModel):
    """One wholesaler candidate with net profit and rank already computed."""

    name: str
    purchase_price_per_kg: float
    purchase_quantity_kg: float
    transport_cost: float
    net_profit: float
    rank: int


class WholesalerOptionExplanation(BaseModel):
    name: str
    rank: int
    explanation: str


class WholesalerRecommendation(BaseModel):
    crop_name: str
    recommended_wholesaler: str
    recommendation_reason: str
    options: list[WholesalerOptionExplanation]


# ---------------------------------------------------------------------------
# 5.3 도매처 맞춤 판매처 연계
# ---------------------------------------------------------------------------

BuyerType = Literal["소매점", "급식업체", "가공업체", "지역음식점"]


class ProduceLot(BaseModel):
    """One batch of produce awaiting a buyer match."""

    lot_id: str
    grade: str  # e.g. "특상품", "가정용", "규격 외"
    quantity_kg: float
    condition_note: str  # e.g. "판매기한 임박", "외관과 크기가 균일함"


class BuyerMatch(BaseModel):
    lot_id: str
    recommended_buyer_type: BuyerType
    reason: str


class BuyerRecommendation(BaseModel):
    matches: list[BuyerMatch]


# ---------------------------------------------------------------------------
# 5.4 지역별 수급 위험 조기 알림
# ---------------------------------------------------------------------------

RiskLevel = Literal["안전", "주의", "위험"]


class ResponseOption(BaseModel):
    """One mitigation channel with the volume it will absorb, already computed."""

    channel: str  # e.g. "식품가공업체 추가 연결"
    processed_volume_ton: float


class SupplyRiskInput(BaseModel):
    region: str
    crop_name: str
    farm_planned_shipment_ton: float
    wholesaler_existing_stock_ton: float
    total_supply_ton: float
    buyer_demand_ton: float
    excess_supply_ton: float
    risk_level: RiskLevel
    response_options: list[ResponseOption]


class ResponsePlanItem(BaseModel):
    channel: str
    rationale: str


class SupplyRiskAlert(BaseModel):
    region: str
    crop_name: str
    risk_level: RiskLevel
    alert_message: str
    situation_explanation: str
    response_plan: list[ResponsePlanItem]


# ---------------------------------------------------------------------------
# 5.6 유휴농지 맞춤형 탐색 및 농업인 연결
# ---------------------------------------------------------------------------


class FarmlandRequest(BaseModel):
    desired_crop: str
    desired_area_pyeong: float
    budget_monthly_rent: float


class FarmlandOption(BaseModel):
    """One farmland candidate with suitability numbers already computed."""

    name: str
    area_pyeong: float
    monthly_rent: float
    water_access: bool
    cold_storage_access: str  # e.g. "가능", "제한적"
    distance_to_wholesaler_km: float
    rank: int


class FarmlandOptionExplanation(BaseModel):
    name: str
    rank: int
    explanation: str


class FarmlandRecommendation(BaseModel):
    recommended_farmland: str
    recommendation_reason: str
    options: list[FarmlandOptionExplanation]


# ---------------------------------------------------------------------------
# 5.5 채팅 어시스턴트 (tool call 포함)
# ---------------------------------------------------------------------------

ChatHistoryMessage = dict[str, str]  # {"role": "user"|"assistant", "content": str}


class ToolCallOutcome(BaseModel):
    """Record of one tool invocation the chat assistant made."""

    name: str
    arguments: dict[str, Any] = Field(default_factory=dict)
    result: dict[str, Any] | None = None
    error: str | None = None


class ChatAssistantResult(BaseModel):
    message: str
    tool_calls: list[ToolCallOutcome] = Field(default_factory=list)
