// Turns a price-forecast response into the "AI 분석 알림" list SPEC 4.2
// shows on the farm dashboard. There is no separate alerts endpoint --
// forecasts already carry the explanation text (summary, per-date
// system_guidance), so alerts are derived rather than invented.

import type { AiAlert, PriceForecastResponse } from "./types"
import { formatDate } from "./format"

export function buildAiAlerts(forecast: PriceForecastResponse): AiAlert[] {
  const now = new Date().toISOString()
  const alerts: AiAlert[] = [
    { id: "forecast-summary", severity: "info", message: forecast.summary, createdAt: now },
    {
      id: "forecast-recommendation",
      severity: "info",
      message: `추천 출하일 ${formatDate(forecast.recommended_date)}: ${forecast.recommendation_reason}`,
      createdAt: now,
    },
  ]

  for (const option of forecast.options) {
    const severity = option.system_guidance.includes("검토") ? "warning" : "info"
    alerts.push({
      id: `forecast-option-${option.date}`,
      severity,
      message: `${formatDate(option.date)} 출하 -- ${option.system_guidance} (${option.market_supply_condition})`,
      createdAt: now,
    })
  }

  return alerts
}
