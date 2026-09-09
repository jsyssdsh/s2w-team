import type { SeriesUpdate } from "@/lib/types"
import { formatKrw, formatPercent } from "@/lib/format"

interface MarketAnalysisPanelProps {
  // Keyed by crop name, straight from the /api/stream/prices SSE feed. Only
  // price and its change percent are shown -- SPEC 4.3 also asks for a
  // demand change percent, but no endpoint or stream provides one, so it is
  // left out rather than invented.
  prices: Record<string, SeriesUpdate>
}

function changeClass(pct: number): string {
  if (pct > 0) return "text-status-good"
  if (pct < 0) return "text-status-bad"
  return "text-ink-muted"
}

export default function MarketAnalysisPanel({ prices }: MarketAnalysisPanelProps) {
  const rows = Object.values(prices).sort((a, b) => a.code.localeCompare(b.code, "ko"))

  if (rows.length === 0) {
    return <p className="text-sm text-ink-muted">실시간 시장 분석 데이터가 없습니다.</p>
  }

  return (
    <div className="divide-y divide-line rounded border border-line bg-paper-raised">
      {rows.map((row) => (
        <div key={row.code} className="flex items-center justify-between px-4 py-2.5 text-sm">
          <span className="font-medium text-ink">{row.code}</span>
          <div className="flex items-center gap-5">
            <span className="font-data text-ink-muted">{formatKrw(row.price)}/kg</span>
            <span className={`font-data w-16 text-right ${changeClass(row.change_percent)}`}>
              {formatPercent(row.change_percent)}
            </span>
          </div>
        </div>
      ))}
    </div>
  )
}
