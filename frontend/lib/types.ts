// Domain types mirroring the backend's Pydantic response models field-for-
// field (snake_case, same names) so there is no translation layer to keep in
// sync -- see the message from the backend agent (SPEC.md section 4-5) for
// the endpoint list these correspond to.

export type ConnectionStatus = "connected" | "connecting" | "disconnected"

export type ConditionGrade = "최상" | "양호" | "개선필요"
export type FarmlandStatus = "idle" | "matched" | "operating"
export type SensorMetric = "temperature" | "humidity" | "soil_moisture" | "light"

export interface Crop {
  id: string
  name: string
  unit: string
}

// --- Farmer -----------------------------------------------------------

export interface ShipmentPlan {
  id: string
  farmer_user_id: string
  smart_farm_id: string | null
  crop_id: string
  crop_name: string
  region: string | null
  expected_yield_kg: number
  planned_shipment_date: string
  grade: string
  status: string
}

export interface SmartFarmOut {
  id: string
  farmland_id: string
  farm_type: string
  operation_start_date: string
  latest_sensor_readings: Partial<Record<SensorMetric, number>>
}

export interface FarmerDashboard {
  farmer_id: string
  farmer_name: string
  shipment_plans: ShipmentPlan[]
  smart_farms: SmartFarmOut[]
}

// --- SPEC 5.1 price forecast --------------------------------------------

export interface PriceForecastOption {
  date: string
  expected_wholesale_price_per_kg: number
  expected_revenue: number
  price_change_percent: number
  market_supply_condition: string
  explanation: string
  system_guidance: string
}

export interface PriceForecastResponse {
  crop_name: string
  summary: string
  recommended_date: string
  recommendation_reason: string
  options: PriceForecastOption[]
}

// --- SPEC 5.2 wholesaler recommendation ----------------------------------

export interface WholesalerOption {
  wholesaler_id: string
  wholesaler_name: string
  purchase_unit_price_krw_per_kg: number
  sellable_quantity_kg: number
  transport_cost_krw: number
  net_profit_krw: number
  rank: number
  explanation: string
}

export interface WholesalerRecommendationResponse {
  crop_name: string
  recommended_wholesaler: string
  recommendation_reason: string
  options: WholesalerOption[]
}

// --- Wholesaler dashboard --------------------------------------------------

export interface RecommendedFarmerShipment {
  shipment_plan_id: string
  farmer_user_id: string
  crop_name: string
  expected_yield_kg: number
  planned_shipment_date: string
  grade: string
  recommended_trade_price_krw_per_kg: number
}

export interface WholesalerDashboard {
  wholesaler_id: string
  wholesaler_name: string
  supply_available_count: number
  ai_recommended_count: number
  expected_amount_krw: number
  recommended_farmer_shipments: RecommendedFarmerShipment[]
}

// --- SPEC 5.3 buyer-type recommendation -----------------------------------

export interface BuyerMatch {
  shipment_plan_id: string
  grade: string
  quantity_kg: number
  recommended_retailer_type: string
  matched_retailer_id: string | null
  matched_retailer_name: string | null
  reason: string
}

export interface BuyerRecommendationResponse {
  matches: BuyerMatch[]
}

// --- SPEC 5.4 supply risk --------------------------------------------------

export interface MitigationAction {
  channel: string
  processed_volume_ton: number
  rationale: string
}

export interface SupplyRiskResponse {
  region: string
  crop_name: string
  farmer_planned_ton: number
  wholesaler_inventory_ton: number
  total_supply_ton: number
  buyer_demand_ton: number
  excess_supply_ton: number
  risk_level: string
  alert_message: string
  situation_explanation: string
  response_plan: MitigationAction[]
}

// --- Farmland (SPEC 4.4 / 4.5 / 5.6) ---------------------------------------

export interface Farmland {
  id: string
  owner_user_id: string
  address: string
  region: string | null
  area_pyeong: number
  monthly_rent_krw: number
  has_water_access: boolean
  has_cold_storage_access: boolean
  distance_to_wholesaler_km: number | null
  soil_status: string | null
  condition_grade: ConditionGrade
  status: FarmlandStatus
  latitude: number | null
  longitude: number | null
}

export interface FarmlandSmartFarmSummary {
  id: string
  farm_type: string
  operation_start_date: string
  latest_sensor_readings: Partial<Record<SensorMetric, number>>
}

export interface FarmlandDetail extends Farmland {
  smart_farm: FarmlandSmartFarmSummary | null
}

export interface FarmlandOption {
  farmland_id: string
  address: string
  area_pyeong: number
  monthly_rent_krw: number
  has_water_access: boolean
  cold_storage_access: string
  distance_to_wholesaler_km: number
  suitability_score: number
  rank: number
  explanation: string
}

export interface FarmlandRecommendationResponse {
  recommended_farmland_id: string
  recommendation_reason: string
  options: FarmlandOption[]
}

// --- Sensors (SPEC 5.5) -----------------------------------------------------

export interface SensorEvaluation {
  metric: SensorMetric
  value: number
  min_value: number | null
  max_value: number | null
  status: string // "정상" | "기준미달" | "기준초과"
  control_action: string | null
}

export interface SensorReadingRow {
  id: string
  smart_farm_id: string
  metric: SensorMetric
  value: number
  unit: string
  measured_at: string
}

// --- Transactions ------------------------------------------------------

export interface Transaction {
  id: string
  shipment_plan_id: string
  wholesaler_id: string | null
  retailer_id: string | null
  counterparty_type: string
  recommendation_id: string | null
  quantity_kg: number
  unit_price_krw_per_kg: number
  transport_cost_krw: number
  commission_krw: number
  net_profit_krw: number | null
  status: string
  requested_at: string
  updated_at: string
}

// --- Chat -----------------------------------------------------------------

export interface ToolCallOutcome {
  name: string
  arguments: Record<string, unknown>
  result: Record<string, unknown> | null
  error: string | null
}

export interface ChatResponse {
  message: string
  tool_calls: ToolCallOutcome[]
  session_id: string
}

export interface ChatHistoryMessage {
  role: string
  content: string
  actions?: ToolCallOutcome[] | null
  created_at?: string
}

// --- Client-derived (not returned directly by any endpoint) ----------------

// SPEC 4.2's "AI 분석 알림" has no dedicated backend endpoint; the farm
// dashboard synthesizes these from a price-forecast response's summary and
// per-date guidance (see lib/ai-alerts.ts) rather than inventing an alerts
// feed.
export interface AiAlert {
  id: string
  severity: "info" | "warning"
  message: string
  createdAt: string
}

// --- Live streams (SSE) -----------------------------------------------------

export interface SeriesUpdate {
  code: string
  price: number
  previous_price: number
  timestamp: number
  change: number
  change_percent: number
  direction: "up" | "down" | "flat"
}

export type SeriesStreamEvent = Record<string, SeriesUpdate>
