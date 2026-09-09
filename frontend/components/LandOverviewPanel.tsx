import type { FarmlandDetail } from "@/lib/types"
import { formatDate, formatKrw, formatPyeong } from "@/lib/format"
import StatusBadge from "@/components/StatusBadge"

interface LandOverviewPanelProps {
  land: FarmlandDetail
}

const STATUS_LABEL: Record<FarmlandDetail["status"], string> = {
  idle: "유휴",
  matched: "매칭 완료",
  operating: "운영 중",
}

export default function LandOverviewPanel({ land }: LandOverviewPanelProps) {
  return (
    <div className="rounded border border-line bg-paper-raised p-5">
      <div className="flex items-center justify-between">
        <h2 className="font-display text-xl font-bold text-ink">{land.address}</h2>
        <StatusBadge grade={land.condition_grade} />
      </div>
      <p className="mt-1 text-sm text-ink-muted">{STATUS_LABEL[land.status]}{land.region ? ` -- ${land.region}` : ""}</p>

      <dl className="mt-4 grid grid-cols-2 gap-4 sm:grid-cols-4">
        <div>
          <dt className="text-xs text-ink-muted">면적</dt>
          <dd className="font-data text-ink">{formatPyeong(land.area_pyeong)}</dd>
        </div>
        <div>
          <dt className="text-xs text-ink-muted">월 임대료</dt>
          <dd className="font-data text-ink">{formatKrw(land.monthly_rent_krw)}</dd>
        </div>
        <div>
          <dt className="text-xs text-ink-muted">농업용수</dt>
          <dd className="text-ink">{land.has_water_access ? "확보" : "미확보"}</dd>
        </div>
        <div>
          <dt className="text-xs text-ink-muted">냉장창고 접근성</dt>
          <dd className="text-ink">{land.has_cold_storage_access ? "가능" : "제한적"}</dd>
        </div>
        {land.distance_to_wholesaler_km !== null && (
          <div>
            <dt className="text-xs text-ink-muted">도매처 거리</dt>
            <dd className="font-data text-ink">{land.distance_to_wholesaler_km}km</dd>
          </div>
        )}
        {land.soil_status && (
          <div className="col-span-2">
            <dt className="text-xs text-ink-muted">토양 상태</dt>
            <dd className="text-ink">{land.soil_status}</dd>
          </div>
        )}
      </dl>

      {land.smart_farm && (
        <dl className="mt-4 grid grid-cols-2 gap-4 border-t border-line pt-3">
          <div>
            <dt className="text-xs text-ink-muted">스마트팜 유형</dt>
            <dd className="text-ink">{land.smart_farm.farm_type}</dd>
          </div>
          <div>
            <dt className="text-xs text-ink-muted">운영 시작일</dt>
            <dd className="font-data text-ink">{formatDate(land.smart_farm.operation_start_date)}</dd>
          </div>
        </dl>
      )}
    </div>
  )
}
