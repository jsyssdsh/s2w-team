import Link from "next/link"
import type { Farmland } from "@/lib/types"
import { formatKrw, formatPyeong } from "@/lib/format"
import StatusBadge from "@/components/StatusBadge"

interface IdleLandCardProps {
  plot: Farmland
}

export default function IdleLandCard({ plot }: IdleLandCardProps) {
  return (
    <Link
      href={`/idle-land/detail?id=${encodeURIComponent(plot.id)}`}
      prefetch={false}
      className="block rounded border border-line bg-paper-raised p-4 transition-colors hover:border-forest"
    >
      <div className="flex items-start justify-between gap-2">
        <h3 className="font-medium text-ink">{plot.address}</h3>
        <StatusBadge grade={plot.condition_grade} />
      </div>
      <dl className="mt-3 grid grid-cols-2 gap-2 text-sm">
        <div>
          <dt className="text-xs text-ink-muted">면적</dt>
          <dd className="font-data text-ink">{formatPyeong(plot.area_pyeong)}</dd>
        </div>
        <div>
          <dt className="text-xs text-ink-muted">월 임대료</dt>
          <dd className="font-data text-ink">{formatKrw(plot.monthly_rent_krw)}</dd>
        </div>
        <div>
          <dt className="text-xs text-ink-muted">농업용수</dt>
          <dd className="text-ink-muted">{plot.has_water_access ? "확보" : "미확보"}</dd>
        </div>
        <div>
          <dt className="text-xs text-ink-muted">냉장창고 접근성</dt>
          <dd className="text-ink-muted">{plot.has_cold_storage_access ? "가능" : "제한적"}</dd>
        </div>
        {plot.soil_status && (
          <div className="col-span-2">
            <dt className="text-xs text-ink-muted">토양 상태</dt>
            <dd className="text-ink-muted">{plot.soil_status}</dd>
          </div>
        )}
      </dl>
    </Link>
  )
}
