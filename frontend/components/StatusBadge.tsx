import type { ConditionGrade } from "@/lib/types"
import { conditionGradeLabel } from "@/lib/condition-grade"

// SPEC 4.4 asks for green/amber/red status color-coding but flags that color
// alone is not accessible -- every badge pairs the color with an icon shape
// and the backend's own condition_grade label so status reads correctly
// without relying on hue.

const STATUS_CONFIG: Record<
  ConditionGrade,
  { colorVar: string; bgVar: string; Icon: (props: { className?: string }) => React.ReactElement }
> = {
  최상: {
    colorVar: "text-status-good",
    bgVar: "bg-status-good/10",
    Icon: (props) => (
      <svg viewBox="0 0 16 16" fill="none" className={props.className} aria-hidden="true">
        <path d="M3 8.5 6.5 12 13 4.5" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
      </svg>
    ),
  },
  양호: {
    colorVar: "text-status-warn",
    bgVar: "bg-status-warn/10",
    Icon: (props) => (
      <svg viewBox="0 0 16 16" fill="none" className={props.className} aria-hidden="true">
        <circle cx="8" cy="8" r="5.5" stroke="currentColor" strokeWidth="2" />
        <path d="M8 5.5v3" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
        <circle cx="8" cy="10.8" r="0.9" fill="currentColor" />
      </svg>
    ),
  },
  개선필요: {
    colorVar: "text-status-bad",
    bgVar: "bg-status-bad/10",
    Icon: (props) => (
      <svg viewBox="0 0 16 16" fill="none" className={props.className} aria-hidden="true">
        <path d="M8 2 14.5 13.5H1.5L8 2Z" stroke="currentColor" strokeWidth="1.6" strokeLinejoin="round" />
        <path d="M8 6.5v3" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />
        <circle cx="8" cy="11.2" r="0.8" fill="currentColor" />
      </svg>
    ),
  },
}

interface StatusBadgeProps {
  grade: ConditionGrade
}

export default function StatusBadge({ grade }: StatusBadgeProps) {
  const config = STATUS_CONFIG[grade]
  const Icon = config.Icon
  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded px-2 py-1 text-xs font-medium ${config.colorVar} ${config.bgVar}`}
    >
      <Icon className="h-3.5 w-3.5" />
      {conditionGradeLabel(grade)}
    </span>
  )
}
