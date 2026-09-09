"""Deterministic mock LLM responses, used when LLM_MOCK=true (no API key needed).

Every mock function takes the same precomputed inputs the real prompt builders
take and formats them into template sentences -- it never invents a number
that wasn't already in the input, mirroring the constraint placed on the real
LLM prompts.
"""

import re

from .models import (
    BuyerMatch,
    BuyerRecommendation,
    ChatAssistantResult,
    FarmlandOption,
    FarmlandOptionExplanation,
    FarmlandRecommendation,
    FarmlandRequest,
    PriceForecastExplanation,
    ProduceLot,
    ResponsePlanItem,
    ShipmentTimingAdvice,
    ShippingDateOption,
    SupplyRiskAlert,
    SupplyRiskInput,
    WholesalerOption,
    WholesalerOptionExplanation,
    WholesalerRecommendation,
)
from .tools import ToolExecutor, execute_tool_call


def mock_price_forecast(
    crop_name: str, options: list[ShippingDateOption]
) -> PriceForecastExplanation:
    advice = []
    for opt in options:
        if opt.price_change_percent > 0:
            guidance = "출하 유지 권장"
            explanation = (
                f"{opt.date}은 기준 대비 {opt.price_change_percent:+.1f}% 상승이 예상되며, "
                f"{opt.market_supply_condition} 상황입니다. 출하를 유지하는 것이 유리합니다."
            )
        elif opt.price_change_percent < 0:
            guidance = "조기 출하 검토"
            explanation = (
                f"{opt.date}은 기준 대비 {opt.price_change_percent:+.1f}% 하락이 예상되며, "
                f"{opt.market_supply_condition} 상황입니다. 조기 출하를 검토하세요."
            )
        else:
            guidance = "즉시 출하 가능"
            explanation = f"{opt.date}은 기준 가격 수준이며, {opt.market_supply_condition} 상황으로 즉시 출하가 가능합니다."
        advice.append(ShipmentTimingAdvice(date=opt.date, explanation=explanation, system_guidance=guidance))

    best = max(options, key=lambda o: o.expected_revenue)
    return PriceForecastExplanation(
        crop_name=crop_name,
        summary=f"{crop_name} 출하일 {len(options)}개 옵션을 비교한 결과입니다.",
        recommended_date=best.date,
        recommendation_reason=(
            f"{best.date} 출하 시 예상 판매금액이 {best.expected_revenue:,.0f}원으로 가장 높습니다."
        ),
        options=advice,
    )


def mock_wholesaler_recommendation(
    crop_name: str, options: list[WholesalerOption]
) -> WholesalerRecommendation:
    explanations = []
    for opt in options:
        explanations.append(
            WholesalerOptionExplanation(
                name=opt.name,
                rank=opt.rank,
                explanation=(
                    f"{opt.name}: 매입단가 {opt.purchase_price_per_kg:,.0f}원/kg, "
                    f"구매량 {opt.purchase_quantity_kg:,.0f}kg, 운송비 {opt.transport_cost:,.0f}원 기준 "
                    f"예상 순수익 {opt.net_profit:,.0f}원으로 {opt.rank}위입니다."
                ),
            )
        )
    top = min(options, key=lambda o: o.rank)
    return WholesalerRecommendation(
        crop_name=crop_name,
        recommended_wholesaler=top.name,
        recommendation_reason=f"{top.name}의 예상 순수익 {top.net_profit:,.0f}원이 가장 높아 가장 유리합니다.",
        options=explanations,
    )


_GRADE_TO_BUYER = (
    ("판매기한 임박", "지역음식점"),
    ("규격 외", "가공업체"),
    ("특", "소매점"),
)


def mock_buyer_recommendation(lots: list[ProduceLot]) -> BuyerRecommendation:
    matches = []
    for lot in lots:
        haystack = f"{lot.grade} {lot.condition_note}"
        buyer_type = "급식업체"
        for keyword, candidate in _GRADE_TO_BUYER:
            if keyword in haystack:
                buyer_type = candidate
                break
        matches.append(
            BuyerMatch(
                lot_id=lot.lot_id,
                recommended_buyer_type=buyer_type,
                reason=f"{lot.grade}({lot.quantity_kg:,.0f}kg, {lot.condition_note}) 상태에 적합합니다.",
            )
        )
    return BuyerRecommendation(matches=matches)


def mock_supply_risk_alert(risk_input: SupplyRiskInput) -> SupplyRiskAlert:
    plan = [
        ResponsePlanItem(
            channel=opt.channel,
            rationale=f"{opt.channel}로 {opt.processed_volume_ton:,.1f}톤을 추가 소진할 수 있습니다.",
        )
        for opt in risk_input.response_options
    ]
    return SupplyRiskAlert(
        region=risk_input.region,
        crop_name=risk_input.crop_name,
        risk_level=risk_input.risk_level,
        alert_message=(
            f"{risk_input.region} {risk_input.crop_name} 공급량이 수요보다 "
            f"{risk_input.excess_supply_ton:,.1f}톤 많아 {risk_input.risk_level} 단계입니다."
        ),
        situation_explanation=(
            f"농가 출하 예정량 {risk_input.farm_planned_shipment_ton:,.1f}톤과 "
            f"도매처 기존 재고 {risk_input.wholesaler_existing_stock_ton:,.1f}톤을 합친 "
            f"전체 공급량 {risk_input.total_supply_ton:,.1f}톤이 "
            f"판매처 구매 수요 {risk_input.buyer_demand_ton:,.1f}톤을 초과합니다."
        ),
        response_plan=plan,
    )


def mock_farmland_recommendation(
    request: FarmlandRequest, options: list[FarmlandOption]
) -> FarmlandRecommendation:
    explanations = []
    for opt in options:
        water = "확보" if opt.water_access else "미확보"
        explanations.append(
            FarmlandOptionExplanation(
                name=opt.name,
                rank=opt.rank,
                explanation=(
                    f"{opt.name}: 면적 {opt.area_pyeong:,.0f}평, 월 임대료 {opt.monthly_rent:,.0f}원, "
                    f"농업용수 {water}, 냉장창고 접근성 {opt.cold_storage_access}, "
                    f"도매처까지 {opt.distance_to_wholesaler_km:.1f}km로 {opt.rank}위입니다."
                ),
            )
        )
    top = min(options, key=lambda o: o.rank)
    return FarmlandRecommendation(
        recommended_farmland=top.name,
        recommendation_reason=(
            f"{request.desired_crop} 재배 희망 조건(약 {request.desired_area_pyeong:,.0f}평, "
            f"월 임대료 {request.budget_monthly_rent:,.0f}원 이내)에 가장 잘 맞습니다."
        ),
        options=explanations,
    )


# Matches e.g. "토마토 500kg B도매처에 거래 요청해줘" or "감자 300kg 하나로컬푸드에 거래 요청"
_CREATE_REQUEST_RE = re.compile(
    r"(?P<crop>\S+?)\s+(?P<quantity>\d+(?:\.\d+)?)\s*kg\D*?(?P<counterparty>\S+?)(?:에게|에)?\s*거래\s*요청"
)
_LIST_REQUEST_KEYWORDS = ("거래 요청 목록", "거래 내역", "요청 확인", "요청 조회")


async def mock_chat(
    user_message: str,
    context: str | None,
    tool_executors: dict[str, ToolExecutor],
) -> ChatAssistantResult:
    """Keyword-driven mock chat. Executes the same injected tool_executors the
    real tool-calling path would, so callers see identical side effects."""
    msg = user_message.strip()

    match = _CREATE_REQUEST_RE.search(msg)
    if match:
        arguments = {
            "crop_name": match.group("crop"),
            "quantity_kg": float(match.group("quantity")),
            "counterparty_name": match.group("counterparty"),
        }
        outcome = await execute_tool_call("create_trade_request", arguments, tool_executors)
        if outcome.error:
            return ChatAssistantResult(
                message=f"거래 요청을 만들지 못했습니다: {outcome.error}", tool_calls=[outcome]
            )
        return ChatAssistantResult(
            message=(
                f"{arguments['crop_name']} {arguments['quantity_kg']:g}kg을 "
                f"{arguments['counterparty_name']}에 거래 요청했습니다."
            ),
            tool_calls=[outcome],
        )

    if any(keyword in msg for keyword in _LIST_REQUEST_KEYWORDS):
        outcome = await execute_tool_call("list_trade_requests", {}, tool_executors)
        if outcome.error:
            return ChatAssistantResult(
                message=f"거래 요청 목록을 불러오지 못했습니다: {outcome.error}", tool_calls=[outcome]
            )
        requests = (outcome.result or {}).get("requests", [])
        return ChatAssistantResult(
            message=f"현재 거래 요청이 {len(requests)}건 있습니다.", tool_calls=[outcome]
        )

    return ChatAssistantResult(
        message=(
            "안녕하세요, 울퉁불퉁 농장 AI 어시스턴트입니다. "
            "시세, 도매처 추천, 거래 요청에 대해 무엇이든 물어보세요."
        ),
    )
