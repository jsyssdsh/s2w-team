// Typed client for the backend REST contract (confirmed by the backend
// agent -- see its message listing every route). Each function targets one
// endpoint 1:1 so a schema change only touches this file.

import type {
  BuyerRecommendationResponse,
  ChatHistoryMessage,
  ChatResponse,
  Crop,
  Farmland,
  FarmlandDetail,
  FarmlandRecommendationResponse,
  FarmerDashboard,
  PriceForecastResponse,
  SensorEvaluation,
  SensorReadingRow,
  ShipmentPlan,
  SupplyRiskResponse,
  Transaction,
  WholesalerDashboard,
  WholesalerRecommendationResponse,
} from "./types"

class ApiError extends Error {
  constructor(message: string, readonly status?: number) {
    super(message)
    this.name = "ApiError"
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(path, {
    headers: { "Content-Type": "application/json" },
    ...init,
  })
  if (!res.ok) {
    const body = await res.text().catch(() => "")
    let message = body || `${path} failed with ${res.status}`
    try {
      const parsed = JSON.parse(body)
      if (typeof parsed?.detail === "string") message = parsed.detail
    } catch {
      // Body wasn't JSON -- keep the raw text message
    }
    throw new ApiError(message, res.status)
  }
  if (res.status === 204) return undefined as T
  return res.json() as Promise<T>
}

function query(params: object): string {
  const usp = new URLSearchParams()
  for (const [key, value] of Object.entries(params) as [string, string | number | boolean | undefined][]) {
    if (value !== undefined) usp.set(key, String(value))
  }
  const qs = usp.toString()
  return qs ? `?${qs}` : ""
}

// --- Crops ------------------------------------------------------------

export function getCrops(): Promise<Crop[]> {
  return request("/api/crops")
}

// --- Farmer -----------------------------------------------------------

export function getFarmerDashboard(farmerId: string): Promise<FarmerDashboard> {
  return request(`/api/farmer/${encodeURIComponent(farmerId)}/dashboard`)
}

export function getShipmentPlans(farmerId: string, status?: string): Promise<ShipmentPlan[]> {
  return request(`/api/farmer/${encodeURIComponent(farmerId)}/shipment-plans${query({ status })}`)
}

export interface ShipmentPlanCreateInput {
  farmer_user_id: string
  crop_id: string
  expected_yield_kg: number
  planned_shipment_date: string
  grade: string
  smart_farm_id?: string | null
  region?: string | null
}

export function createShipmentPlan(input: ShipmentPlanCreateInput): Promise<ShipmentPlan> {
  return request("/api/farmer/shipment-plans", {
    method: "POST",
    body: JSON.stringify(input),
  })
}

export function getPriceForecast(shipmentPlanId: string, candidateDates?: string[]): Promise<PriceForecastResponse> {
  return request("/api/farmer/price-forecast", {
    method: "POST",
    body: JSON.stringify({ shipment_plan_id: shipmentPlanId, candidate_dates: candidateDates ?? null }),
  })
}

export function getWholesalerRecommendation(shipmentPlanId: string): Promise<WholesalerRecommendationResponse> {
  return request("/api/farmer/wholesaler-recommendation", {
    method: "POST",
    body: JSON.stringify({ shipment_plan_id: shipmentPlanId }),
  })
}

// --- Wholesaler ---------------------------------------------------------

export function getWholesalerDashboard(wholesalerId: string): Promise<WholesalerDashboard> {
  return request(`/api/wholesaler/${encodeURIComponent(wholesalerId)}/dashboard`)
}

export function getBuyerRecommendation(shipmentPlanIds: string[]): Promise<BuyerRecommendationResponse> {
  return request("/api/wholesaler/buyer-recommendation", {
    method: "POST",
    body: JSON.stringify({ shipment_plan_ids: shipmentPlanIds }),
  })
}

// --- Supply risk (SPEC 5.4) ------------------------------------------------

export function getSupplyRisk(cropName: string, region: string): Promise<SupplyRiskResponse> {
  return request("/api/supply-risk", {
    method: "POST",
    body: JSON.stringify({ crop_name: cropName, region }),
  })
}

// --- Farmland (SPEC 4.4 / 4.5 / 5.6) ---------------------------------------

export interface FarmlandFilters {
  region?: string
  status?: string
  min_area_pyeong?: number
  max_area_pyeong?: number
  max_monthly_rent_krw?: number
  require_water_access?: boolean
  require_cold_storage_access?: boolean
}

export function listFarmlands(filters: FarmlandFilters = {}): Promise<Farmland[]> {
  return request(`/api/farmlands${query(filters)}`)
}

export function getFarmlandDetail(id: string): Promise<FarmlandDetail> {
  return request(`/api/farmlands/${encodeURIComponent(id)}`)
}

export interface FarmlandRecommendationInput {
  user_id: string
  desired_crop: string
  desired_area_pyeong: number
  budget_monthly_rent_krw: number
  region?: string
}

export function getFarmlandRecommendation(
  input: FarmlandRecommendationInput
): Promise<FarmlandRecommendationResponse> {
  return request("/api/farmlands/recommendation", {
    method: "POST",
    body: JSON.stringify(input),
  })
}

// --- Sensors (SPEC 5.5) ------------------------------------------------

export function getLatestSensorReadings(smartFarmId: string, cropId?: string): Promise<SensorEvaluation[]> {
  return request(`/api/smart-farms/${encodeURIComponent(smartFarmId)}/sensors/latest${query({ crop_id: cropId })}`)
}

export function getSensorHistory(
  smartFarmId: string,
  metric: string,
  start: string,
  end: string
): Promise<SensorReadingRow[]> {
  return request(
    `/api/smart-farms/${encodeURIComponent(smartFarmId)}/sensors/history${query({ metric, start, end })}`
  )
}

// --- Transactions ------------------------------------------------------

export interface TransactionCreateInput {
  shipment_plan_id: string
  counterparty_type: "wholesaler" | "retailer"
  quantity_kg: number
  unit_price_krw_per_kg: number
  wholesaler_id?: string | null
  retailer_id?: string | null
  recommendation_id?: string | null
  transport_cost_krw?: number
  commission_rate?: number
}

export function createTransaction(input: TransactionCreateInput): Promise<Transaction> {
  return request("/api/transactions", {
    method: "POST",
    body: JSON.stringify(input),
  })
}

export function listTransactions(shipmentPlanId: string): Promise<Transaction[]> {
  return request(`/api/transactions${query({ shipment_plan_id: shipmentPlanId })}`)
}

export function updateTransactionStatus(id: string, status: string): Promise<Transaction> {
  return request(`/api/transactions/${encodeURIComponent(id)}/status`, {
    method: "PATCH",
    body: JSON.stringify({ status }),
  })
}

// --- Chat ------------------------------------------------------------------

// session_id separates chat history per browser tab (see lib/chat-session.ts)
// and is unrelated to user_id, which selects whose shipment plans/trades the
// chat's tools act on -- left at its backend default (the seeded demo
// farmer) since there is no login yet (confirmed with backend: ChatRequest
// keeps the two fields independent, chat.py routes them to separate keys).
export function sendChatMessage(message: string, sessionId: string): Promise<ChatResponse> {
  return request("/api/chat", {
    method: "POST",
    body: JSON.stringify({ message, session_id: sessionId }),
  })
}

export function getChatHistory(sessionId: string): Promise<ChatHistoryMessage[]> {
  return request(`/api/chat/history${query({ session_id: sessionId })}`)
}

export { ApiError }
