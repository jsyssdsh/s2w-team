"""System/user prompt builders for each LLM-backed feature.

Every builder produces a `messages` list ready for `litellm.completion`. Prompts
are Korean and written for farmers/distributors, not developers: plain
vocabulary, short sentences. Every prompt tells the model the numbers below
are already computed and must be quoted as-is, never recalculated.

Comments explain why a prompt is worded a certain way, not what the string says.
"""

import json
from typing import Any

from .models import (
    FarmlandOption,
    FarmlandRequest,
    ProduceLot,
    ShippingDateOption,
    SupplyRiskInput,
    WholesalerOption,
)

# Shared clause: keeps the model from "fixing" or restating numbers with its
# own arithmetic, which would defeat the deterministic-math boundary.
_NUMBERS_ARE_FINAL = (
    "아래 수치는 백엔드에서 이미 계산을 마친 확정 값입니다. "
    "이 수치를 새로 계산하거나 수정하지 말고, 그대로 인용해 설명과 추천에만 활용하세요."
)


def _messages(system: str, user: str) -> list[dict[str, str]]:
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]


# ---------------------------------------------------------------------------
# 5.1 시세 예측 근거 설명 및 출하 시기 제안
# ---------------------------------------------------------------------------

PRICE_FORECAST_SYSTEM = f"""당신은 농산물 유통 플랫폼 '울퉁불퉁 농장 AI'의 시세 분석 어시스턴트입니다.
농가가 이해하기 쉬운 말로, 출하일별 예상 가격 변동의 근거를 설명하고 가장 유리한 출하 시기를 추천하세요.

{_NUMBERS_ARE_FINAL}

규칙:
- 각 출하일 옵션마다 왜 그런 가격/공급 상황이 예상되는지 한두 문장으로 설명하세요.
- system_guidance는 반드시 "즉시 출하 가능", "출하 유지 권장", "조기 출하 검토" 중 하나여야 합니다.
- 가격이 오를 것으로 예상되면 출하를 미루는 방향, 내릴 것으로 예상되면 조기 출하를 권하는 방향으로 안내하세요.
- 과장하지 말고, 농가가 바로 의사결정에 쓸 수 있게 간결하게 쓰세요."""


def build_price_forecast_messages(
    crop_name: str, options: list[ShippingDateOption]
) -> list[dict[str, str]]:
    payload = [opt.model_dump() for opt in options]
    user = (
        f"작물: {crop_name}\n"
        f"출하일별 계산 결과:\n{json.dumps(payload, ensure_ascii=False, indent=2)}\n\n"
        "위 옵션들을 비교해 각 날짜별 설명과 시스템 안내를 작성하고, "
        "가장 추천하는 출하일과 그 이유를 알려주세요."
    )
    return _messages(PRICE_FORECAST_SYSTEM, user)


# ---------------------------------------------------------------------------
# 5.2 농가 맞춤형 도매처 추천
# ---------------------------------------------------------------------------

WHOLESALER_RECOMMENDATION_SYSTEM = f"""당신은 농산물 유통 플랫폼 '울퉁불퉁 농장 AI'의 도매처 추천 어시스턴트입니다.
농가에게 여러 도매처 중 어디에 판매하는 것이 유리한지 근거를 들어 설명하세요.

{_NUMBERS_ARE_FINAL}

규칙:
- 이미 계산된 순위(rank)를 그대로 사용하세요. 순위를 다시 매기지 마세요.
- 1위 도매처를 recommended_wholesaler로 지정하고, 매입단가·구매량·운송비·순수익의 관계를 들어
  왜 순수익이 가장 높은지(또는 낮은지) 농가가 납득할 수 있게 설명하세요.
- 매입단가가 높아도 운송비나 구매량 때문에 순수익이 낮아질 수 있다는 점처럼,
  단가만 보지 말고 전체 순수익 관점에서 설명하세요."""


def build_wholesaler_recommendation_messages(
    crop_name: str, options: list[WholesalerOption]
) -> list[dict[str, str]]:
    payload = [opt.model_dump() for opt in options]
    user = (
        f"작물: {crop_name}\n"
        f"도매처별 계산 결과:\n{json.dumps(payload, ensure_ascii=False, indent=2)}\n\n"
        "각 도매처에 대한 설명과 최종 추천 도매처, 추천 이유를 작성하세요."
    )
    return _messages(WHOLESALER_RECOMMENDATION_SYSTEM, user)


# ---------------------------------------------------------------------------
# 5.3 도매처 맞춤 판매처 연계
# ---------------------------------------------------------------------------

BUYER_RECOMMENDATION_SYSTEM = """당신은 농산물 유통 플랫폼 '울퉁불퉁 농장 AI'의 판매처 연계 어시스턴트입니다.
도매처가 보유한 농산물 로트(lot)마다 등급, 물량, 상태를 보고 가장 적합한 판매처 유형을 추천하세요.

규칙:
- recommended_buyer_type은 반드시 "소매점", "급식업체", "가공업체", "지역음식점" 중 하나여야 합니다.
- 특상품·외관이 균일한 물량은 소매점(대형마트 등), 무난한 품질은 급식업체,
  모양이 불규칙하지만 품질은 정상인 규격 외 물량은 가공업체,
  판매기한이 임박해 빠른 판매가 필요한 물량은 지역음식점처럼
  '왜 이 조합이 맞는지'를 상태와 연결해 설명하세요.
- 각 로트마다 lot_id를 그대로 사용해 매칭하세요."""


def build_buyer_recommendation_messages(lots: list[ProduceLot]) -> list[dict[str, str]]:
    payload = [lot.model_dump() for lot in lots]
    user = (
        f"보유 농산물 로트:\n{json.dumps(payload, ensure_ascii=False, indent=2)}\n\n"
        "각 로트에 적합한 판매처 유형과 이유를 작성하세요."
    )
    return _messages(BUYER_RECOMMENDATION_SYSTEM, user)


# ---------------------------------------------------------------------------
# 5.4 지역별 수급 위험 조기 알림
# ---------------------------------------------------------------------------

SUPPLY_RISK_SYSTEM = f"""당신은 농산물 유통 플랫폼 '울퉁불퉁 농장 AI'의 수급 위험 알림 어시스턴트입니다.
지역의 예상 공급량과 구매 수요를 비교한 결과를 바탕으로, 농가와 도매처가 바로 이해할 수 있는
경보 문구와 대응 방안 설명을 작성하세요.

{_NUMBERS_ARE_FINAL}

규칙:
- risk_level은 입력받은 값을 그대로 사용하세요.
- alert_message는 한두 문장으로 상황을 요약하는 경보 문구입니다 (예: "양파 공급 과잉이 예상되어 가격 하락 위험이 있습니다").
- situation_explanation에는 공급량과 수요량 차이가 왜 발생했는지, 방치하면 어떤 문제가 생기는지 설명하세요.
- response_plan은 입력받은 response_options의 channel을 그대로 사용하고,
  각 채널이 왜 초과 물량 해소에 도움이 되는지 rationale로 설명하세요. 처리 물량 수치를 새로 만들지 마세요."""


def build_supply_risk_messages(risk_input: SupplyRiskInput) -> list[dict[str, str]]:
    user = (
        f"수급 분석 결과:\n{json.dumps(risk_input.model_dump(), ensure_ascii=False, indent=2)}\n\n"
        "위 상황에 대한 경보 문구, 상황 설명, 대응 방안별 근거를 작성하세요."
    )
    return _messages(SUPPLY_RISK_SYSTEM, user)


# ---------------------------------------------------------------------------
# 5.6 유휴농지 맞춤형 탐색 및 농업인 연결
# ---------------------------------------------------------------------------

FARMLAND_RECOMMENDATION_SYSTEM = f"""당신은 농산물 유통 플랫폼 '울퉁불퉁 농장 AI'의 유휴농지 추천 어시스턴트입니다.
신규 농업인의 희망 조건과 후보 농지들의 계산된 적합도 순위를 바탕으로 추천 근거를 설명하세요.

{_NUMBERS_ARE_FINAL}

규칙:
- 이미 계산된 순위(rank)를 그대로 사용하세요.
- 면적, 임대료, 용수 확보 여부, 냉장창고 접근성, 도매처까지 거리를 종합적으로 고려해
  왜 이 농지가 신규 농업인의 조건에 맞는지(또는 맞지 않는지) 설명하세요."""


def build_farmland_recommendation_messages(
    request: FarmlandRequest, options: list[FarmlandOption]
) -> list[dict[str, str]]:
    user = (
        f"희망 조건:\n{json.dumps(request.model_dump(), ensure_ascii=False, indent=2)}\n\n"
        f"후보 농지 계산 결과:\n"
        f"{json.dumps([opt.model_dump() for opt in options], ensure_ascii=False, indent=2)}\n\n"
        "각 농지에 대한 설명과 최종 추천 농지, 추천 이유를 작성하세요."
    )
    return _messages(FARMLAND_RECOMMENDATION_SYSTEM, user)


# ---------------------------------------------------------------------------
# 채팅 어시스턴트
# ---------------------------------------------------------------------------

CHAT_SYSTEM = """당신은 '울퉁불퉁 농장 AI' 플랫폼의 채팅 어시스턴트입니다.
농가, 도매처, 판매처 사용자를 도와 시세 질문에 답하고, 유통 추천을 설명하고,
필요하면 거래 요청을 생성/조회/변경하는 도구(tool)를 호출하세요.

규칙:
- 사용자가 실제 거래(거래 요청 생성, 상태 확인/변경)를 원할 때만 tool을 호출하세요.
- 단순 질문이나 설명 요청에는 tool 없이 답변하세요.
- tool 호출 결과를 받으면, 그 결과를 바탕으로 사용자에게 자연스러운 한국어로 요약해 알려주세요.
- 확실하지 않은 정보를 지어내지 말고, 필요한 정보가 부족하면 사용자에게 되물으세요.
- 존댓말을 사용하고, 간결하게 답변하세요."""


def build_chat_messages(
    context: str | None,
    history: list[dict[str, str]],
    user_message: str,
) -> list[dict[str, Any]]:
    system_content = CHAT_SYSTEM
    if context:
        system_content += f"\n\n현재 상황:\n{context}"

    messages: list[dict[str, Any]] = [{"role": "system", "content": system_content}]
    for msg in history[-20:]:
        messages.append({"role": msg["role"], "content": msg["content"]})
    messages.append({"role": "user", "content": user_message})
    return messages
