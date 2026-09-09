// Shared summary-stat strip: distributor dashboard shows 3 figures, idle-land
// map shows 4 -- same visual treatment (big mono number, small label), so one
// component renders both instead of duplicating the layout per screen.

export interface Stat {
  label: string
  value: string
  accent?: "forest" | "wheat" | "ink"
}

const ACCENT_CLASS: Record<NonNullable<Stat["accent"]>, string> = {
  forest: "text-forest-deep",
  wheat: "text-wheat",
  ink: "text-ink",
}

interface StatRowProps {
  stats: Stat[]
}

export default function StatRow({ stats }: StatRowProps) {
  return (
    <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
      {stats.map((stat) => (
        <div key={stat.label} className="rounded border border-line bg-paper-raised px-4 py-3">
          <div className="text-xs text-ink-muted">{stat.label}</div>
          <div className={`font-data text-2xl font-medium ${ACCENT_CLASS[stat.accent ?? "ink"]}`}>
            {stat.value}
          </div>
        </div>
      ))}
    </div>
  )
}
