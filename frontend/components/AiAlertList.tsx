import type { AiAlert } from "@/lib/types"
import { formatTime } from "@/lib/format"

const SEVERITY_STYLE: Record<AiAlert["severity"], string> = {
  info: "border-forest/30 text-forest-deep",
  warning: "border-status-warn/40 text-status-warn",
}

const SEVERITY_LABEL: Record<AiAlert["severity"], string> = {
  info: "안내",
  warning: "주의",
}

interface AiAlertListProps {
  alerts: AiAlert[]
}

export default function AiAlertList({ alerts }: AiAlertListProps) {
  if (alerts.length === 0) {
    return <p className="text-sm text-ink-muted">현재 표시할 AI 분석 알림이 없습니다.</p>
  }

  return (
    <ul className="space-y-2">
      {alerts.map((alert) => (
        <li
          key={alert.id}
          className={`rounded border-l-4 bg-paper-raised px-3 py-2 text-sm ${SEVERITY_STYLE[alert.severity]}`}
        >
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium">{SEVERITY_LABEL[alert.severity]}</span>
            <span className="text-xs text-ink-faint">{formatTime(alert.createdAt)}</span>
          </div>
          <p className="mt-0.5 text-ink">{alert.message}</p>
        </li>
      ))}
    </ul>
  )
}
