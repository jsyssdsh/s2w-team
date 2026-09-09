import Link from "next/link"
import type { Farmland } from "@/lib/types"
import StatusBadge from "@/components/StatusBadge"
import { conditionGradeLabel } from "@/lib/condition-grade"

interface IdleLandMapProps {
  plots: Farmland[]
}

function hasCoordinates(plot: Farmland): plot is Farmland & { latitude: number; longitude: number } {
  return plot.latitude !== null && plot.longitude !== null
}

function ScatterMap({ plots }: { plots: (Farmland & { latitude: number; longitude: number })[] }) {
  const lats = plots.map((p) => p.latitude)
  const lngs = plots.map((p) => p.longitude)
  const latRange = [Math.min(...lats), Math.max(...lats)] as const
  const lngRange = [Math.min(...lngs), Math.max(...lngs)] as const
  const latSpan = latRange[1] - latRange[0] || 1
  const lngSpan = lngRange[1] - lngRange[0] || 1

  return (
    <div
      role="img"
      aria-label="유휴토지 위치와 상태를 나타낸 지도"
      className="field-grid relative h-80 overflow-hidden rounded border border-line bg-paper-raised"
    >
      {plots.map((plot) => {
        const x = 8 + ((plot.longitude - lngRange[0]) / lngSpan) * 84
        const y = 8 + (1 - (plot.latitude - latRange[0]) / latSpan) * 84
        return (
          <Link
            key={plot.id}
            href={`/idle-land/detail?id=${encodeURIComponent(plot.id)}`}
            prefetch={false}
            aria-label={`${plot.address}, ${conditionGradeLabel(plot.condition_grade)}`}
            title={`${plot.address} (${plot.condition_grade})`}
            className="group absolute flex -translate-x-1/2 -translate-y-1/2 flex-col items-center"
            style={{ left: `${x}%`, top: `${y}%` }}
          >
            <span
              className={`h-3.5 w-3.5 rounded-full border-2 border-paper-raised shadow-sm transition-transform group-hover:scale-125 ${
                plot.condition_grade === "최상"
                  ? "bg-status-good"
                  : plot.condition_grade === "양호"
                  ? "bg-status-warn"
                  : "bg-status-bad"
              }`}
            />
            <span className="mt-1 whitespace-nowrap rounded bg-ink px-1.5 py-0.5 text-[10px] text-paper-raised opacity-0 transition-opacity group-hover:opacity-100">
              {plot.address}
            </span>
          </Link>
        )
      })}
    </div>
  )
}

function RegionList({ plots }: { plots: Farmland[] }) {
  const byRegion = new Map<string, Farmland[]>()
  for (const plot of plots) {
    const key = plot.region ?? "지역 미상"
    byRegion.set(key, [...(byRegion.get(key) ?? []), plot])
  }

  return (
    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
      {[...byRegion.entries()].map(([region, regionPlots]) => (
        <div key={region} className="rounded border border-line bg-paper-raised p-4">
          <h3 className="mb-2 text-sm font-medium text-ink-muted">
            {region} <span className="text-ink-faint">({regionPlots.length}건)</span>
          </h3>
          <ul className="space-y-1.5">
            {regionPlots.map((plot) => (
              <li key={plot.id}>
                <Link
                  href={`/idle-land/detail?id=${encodeURIComponent(plot.id)}`}
                  prefetch={false}
                  className="flex items-center justify-between gap-2 rounded px-2 py-1.5 text-sm text-ink transition-colors hover:bg-forest-tint"
                >
                  <span className="truncate">{plot.address}</span>
                  <StatusBadge grade={plot.condition_grade} />
                </Link>
              </li>
            ))}
          </ul>
        </div>
      ))}
    </div>
  )
}

export default function IdleLandMap({ plots }: IdleLandMapProps) {
  if (plots.length === 0) {
    return (
      <div className="flex h-40 items-center justify-center rounded border border-dashed border-line text-sm text-ink-muted">
        표시할 유휴토지가 없습니다
      </div>
    )
  }

  // Plot real coordinates when every farmland has them; otherwise fall back
  // to grouping by region rather than mixing placed and unplaced markers.
  if (plots.every(hasCoordinates)) {
    return <ScatterMap plots={plots} />
  }
  return <RegionList plots={plots} />
}
