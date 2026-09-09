"use client"

interface QuickActionBarProps {
  onRegisterCrop: () => void
  onRefreshWholesalerRecommendation: () => void
  onRefreshPriceForecast: () => void
  onShowTransactions: () => void
  busy?: boolean
}

export default function QuickActionBar({
  onRegisterCrop,
  onRefreshWholesalerRecommendation,
  onRefreshPriceForecast,
  onShowTransactions,
  busy,
}: QuickActionBarProps) {
  const actions = [
    { label: "작물 등록", onClick: onRegisterCrop },
    { label: "AI 유통 추천", onClick: onRefreshWholesalerRecommendation },
    { label: "가격 분석", onClick: onRefreshPriceForecast },
    { label: "거래 현황", onClick: onShowTransactions },
  ]

  return (
    <div className="flex flex-wrap gap-2">
      {actions.map((action) => (
        <button
          key={action.label}
          type="button"
          onClick={action.onClick}
          disabled={busy}
          className="rounded border border-line bg-paper-raised px-3 py-1.5 text-sm text-ink transition-colors hover:border-forest hover:text-forest-deep disabled:cursor-not-allowed disabled:opacity-50"
        >
          {action.label}
        </button>
      ))}
    </div>
  )
}
