"use client"

import { CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts"
import type { SensorReadingRow } from "@/lib/types"
import { formatTime } from "@/lib/format"

interface SensorHistoryChartProps {
  rows: SensorReadingRow[]
}

// GET .../sensors/history takes one metric per call, so this charts one
// series at a time -- the caller (idle-land detail page) offers a metric
// switcher and refetches rather than trying to merge four independently
// timestamped series onto one axis.
export default function SensorHistoryChart({ rows }: SensorHistoryChartProps) {
  if (rows.length < 2) {
    return (
      <div className="flex h-56 items-center justify-center rounded border border-dashed border-line text-xs text-ink-muted">
        센서 변화 데이터를 불러오는 중입니다
      </div>
    )
  }

  const chartData = rows.map((row) => ({
    time: formatTime(row.measured_at),
    value: row.value,
  }))
  const unit = rows[0].unit

  return (
    <div className="h-56 rounded border border-line bg-paper-raised p-3">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" stroke="#d9d2bc" vertical={false} />
          <XAxis dataKey="time" tick={{ fill: "#6e6858", fontSize: 11 }} stroke="#d9d2bc" />
          <YAxis
            tick={{ fill: "#6e6858", fontSize: 11 }}
            stroke="#d9d2bc"
            width={44}
            tickFormatter={(v) => `${v}${unit}`}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: "#faf7ee",
              border: "1px solid #d9d2bc",
              borderRadius: "4px",
              fontSize: "12px",
              color: "#262420",
            }}
            formatter={(value) => [`${value}${unit}`, "측정값"]}
          />
          <Line type="monotone" dataKey="value" stroke="#2f5233" strokeWidth={2} dot={false} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}
