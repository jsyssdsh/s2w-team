"use client"

import { useState } from "react"
import type { RecommendedFarmerShipment } from "@/lib/types"
import { formatDate, formatKg, formatKrw } from "@/lib/format"
import { createTransaction, ApiError } from "@/lib/api"

interface RecommendedShipmentListProps {
  shipments: RecommendedFarmerShipment[]
  wholesalerId: string
}

export default function RecommendedShipmentList({ shipments, wholesalerId }: RecommendedShipmentListProps) {
  const [requestState, setRequestState] = useState<Record<string, "sending" | "sent" | "error">>({})

  async function handleRequest(shipment: RecommendedFarmerShipment) {
    setRequestState((prev) => ({ ...prev, [shipment.shipment_plan_id]: "sending" }))
    try {
      await createTransaction({
        shipment_plan_id: shipment.shipment_plan_id,
        counterparty_type: "wholesaler",
        wholesaler_id: wholesalerId,
        quantity_kg: shipment.expected_yield_kg,
        unit_price_krw_per_kg: shipment.recommended_trade_price_krw_per_kg,
      })
      setRequestState((prev) => ({ ...prev, [shipment.shipment_plan_id]: "sent" }))
    } catch (err) {
      setRequestState((prev) => ({ ...prev, [shipment.shipment_plan_id]: "error" }))
      if (err instanceof ApiError) {
        // Surfaced inline per-row below; nothing further to do here.
      }
    }
  }

  if (shipments.length === 0) {
    return <p className="text-sm text-ink-muted">추천 가능한 농가 출하 계획이 아직 없습니다.</p>
  }

  return (
    <div className="overflow-x-auto rounded border border-line">
      <table className="w-full min-w-[640px] text-sm">
        <thead>
          <tr className="border-b border-line bg-paper-raised text-left text-xs text-ink-muted">
            <th className="px-3 py-2 font-normal">품목</th>
            <th className="px-3 py-2 font-normal">등급</th>
            <th className="px-3 py-2 font-normal text-right">출하량</th>
            <th className="px-3 py-2 font-normal">출하 예정일</th>
            <th className="px-3 py-2 font-normal text-right">권장 거래가</th>
            <th className="px-3 py-2 font-normal"></th>
          </tr>
        </thead>
        <tbody>
          {shipments.map((shipment) => {
            const state = requestState[shipment.shipment_plan_id]
            return (
              <tr
                key={shipment.shipment_plan_id}
                className="border-b border-line last:border-0 hover:bg-forest-tint/40"
              >
                <td className="px-3 py-2 font-medium text-ink">{shipment.crop_name}</td>
                <td className="px-3 py-2 text-ink-muted">{shipment.grade}</td>
                <td className="px-3 py-2 text-right font-data text-ink-muted">
                  {formatKg(shipment.expected_yield_kg)}
                </td>
                <td className="px-3 py-2 text-ink-muted">{formatDate(shipment.planned_shipment_date)}</td>
                <td className="px-3 py-2 text-right font-data font-medium text-status-good">
                  {formatKrw(shipment.recommended_trade_price_krw_per_kg)}/kg
                </td>
                <td className="px-3 py-2 text-right">
                  <button
                    type="button"
                    onClick={() => handleRequest(shipment)}
                    disabled={state === "sending" || state === "sent"}
                    className="whitespace-nowrap rounded border border-forest px-2.5 py-1 text-xs font-medium text-forest-deep transition-colors hover:bg-forest hover:text-paper-raised disabled:cursor-not-allowed disabled:opacity-60 disabled:hover:bg-transparent disabled:hover:text-forest-deep"
                  >
                    {state === "sending" ? "전송 중..." : state === "sent" ? "요청 완료" : "거래 요청 보내기"}
                  </button>
                  {state === "error" && (
                    <div className="mt-1 text-[11px] text-status-bad">전송 실패, 다시 시도하세요</div>
                  )}
                </td>
              </tr>
            )
          })}
        </tbody>
      </table>
    </div>
  )
}
