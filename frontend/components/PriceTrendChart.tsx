"use client"

import { Area, AreaChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts"
import type { PriceForecastOption } from "@/lib/types"
import { formatDate, formatKrw } from "@/lib/format"

interface PriceTrendChartProps {
  options: PriceForecastOption[]
  crop: string
  recommendedDate: string
}

export default function PriceTrendChart({ options, crop, recommendedDate }: PriceTrendChartProps) {
  if (options.length < 2) {
    return (
      <div className="flex h-56 items-center justify-center rounded border border-dashed border-line text-xs text-ink-muted">
        시세 데이터를 불러오는 중입니다
      </div>
    )
  }

  const chartData = options.map((o) => ({
    date: formatDate(o.date),
    price: o.expected_wholesale_price_per_kg,
    recommended: o.date === recommendedDate,
  }))

  return (
    <div className="h-56 rounded border border-line bg-paper-raised p-3">
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" stroke="#d9d2bc" vertical={false} />
          <XAxis dataKey="date" tick={{ fill: "#6e6858", fontSize: 11 }} stroke="#d9d2bc" />
          <YAxis
            tick={{ fill: "#6e6858", fontSize: 11 }}
            stroke="#d9d2bc"
            tickFormatter={(v) => `${(v / 1000).toFixed(1)}천원`}
            width={56}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: "#faf7ee",
              border: "1px solid #d9d2bc",
              borderRadius: "4px",
              fontSize: "12px",
              color: "#262420",
            }}
            formatter={(value) => [formatKrw(value as number), `${crop} 예상 도매가`]}
          />
          <Area
            type="monotone"
            dataKey="price"
            stroke="#2f5233"
            fill="rgba(47, 82, 51, 0.12)"
            strokeWidth={2}
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  )
}
