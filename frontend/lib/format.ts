// Formatting helpers for Korean-won currency and farm data. Centralized so
// every screen renders numbers the same way.

export function formatKrw(value: number): string {
  return new Intl.NumberFormat("ko-KR", {
    style: "currency",
    currency: "KRW",
    maximumFractionDigits: 0,
  }).format(value)
}

export function formatPercent(value: number): string {
  const sign = value >= 0 ? "+" : ""
  return `${sign}${value.toFixed(1)}%`
}

export function formatKg(value: number): string {
  return `${new Intl.NumberFormat("ko-KR").format(value)}kg`
}

export function formatPyeong(value: number): string {
  return `${new Intl.NumberFormat("ko-KR").format(value)}평`
}

export function formatDate(value: string): string {
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value
  return new Intl.DateTimeFormat("ko-KR", { month: "long", day: "numeric" }).format(date)
}

export function formatTime(value: string): string {
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value
  return new Intl.DateTimeFormat("ko-KR", { hour: "2-digit", minute: "2-digit" }).format(date)
}
