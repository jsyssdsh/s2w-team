import type { WholesalerOption } from "@/lib/types"
import { formatKrw } from "@/lib/format"

interface WholesalerRecommendationListProps {
  options: WholesalerOption[]
}

export default function WholesalerRecommendationList({ options }: WholesalerRecommendationListProps) {
  if (options.length === 0) {
    return <p className="text-sm text-ink-muted">추천 가능한 도매처가 아직 없습니다.</p>
  }

  const sorted = [...options].sort((a, b) => a.rank - b.rank)

  return (
    <ol className="space-y-2">
      {sorted.map((option) => (
        <li
          key={option.wholesaler_id}
          className={`rounded border px-4 py-3 ${
            option.rank === 1 ? "border-forest bg-forest-tint" : "border-line bg-paper-raised"
          }`}
        >
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="font-data text-xs text-ink-muted">{option.rank}순위</span>
              <span className="font-medium text-ink">{option.wholesaler_name}</span>
            </div>
            <span className="font-data text-base font-medium text-status-good">
              순수익 {formatKrw(option.net_profit_krw)}
            </span>
          </div>
          <div className="mt-1 flex flex-wrap gap-x-4 gap-y-0.5 text-xs text-ink-muted">
            <span>매입단가 {formatKrw(option.purchase_unit_price_krw_per_kg)}/kg</span>
            <span>구매 가능량 {option.sellable_quantity_kg.toLocaleString("ko-KR")}kg</span>
            <span>운송비 {formatKrw(option.transport_cost_krw)}</span>
          </div>
          <p className="mt-1.5 text-sm text-ink-muted">{option.explanation}</p>
        </li>
      ))}
    </ol>
  )
}
