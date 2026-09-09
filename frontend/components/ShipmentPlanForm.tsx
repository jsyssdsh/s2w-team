"use client"

import { useEffect, useState } from "react"
import type { Crop, ShipmentPlan } from "@/lib/types"
import { createShipmentPlan, getCrops, ApiError } from "@/lib/api"

const GRADES = ["특상품", "상품", "규격외", "판매기한임박"]

interface ShipmentPlanFormProps {
  farmerId: string
  onCreated: (plan: ShipmentPlan) => void
  onCancel: () => void
}

export default function ShipmentPlanForm({ farmerId, onCreated, onCancel }: ShipmentPlanFormProps) {
  const [crops, setCrops] = useState<Crop[]>([])
  const [cropId, setCropId] = useState("")
  const [yieldKg, setYieldKg] = useState("")
  const [date, setDate] = useState("")
  const [grade, setGrade] = useState(GRADES[0])
  const [region, setRegion] = useState("")
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    getCrops()
      .then((list) => {
        setCrops(list)
        if (list.length > 0) setCropId(list[0].id)
      })
      .catch(() => {
        // Crop dropdown will just stay empty; the form is unusable but
        // visibly so rather than silently defaulting to a made-up crop.
      })
  }, [])

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    const parsedYield = parseFloat(yieldKg)
    if (!cropId || !date || !parsedYield || parsedYield <= 0) {
      setError("작물, 예상 수확량, 출하 예정일을 입력하세요")
      return
    }
    setSubmitting(true)
    setError(null)
    try {
      const plan = await createShipmentPlan({
        farmer_user_id: farmerId,
        crop_id: cropId,
        expected_yield_kg: parsedYield,
        planned_shipment_date: date,
        grade,
        region: region || null,
      })
      onCreated(plan)
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "출하 계획 등록에 실패했습니다")
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <form
      aria-label="작물 등록"
      onSubmit={handleSubmit}
      className="rounded border border-line bg-paper-raised p-4"
    >
      <div className="grid gap-3 sm:grid-cols-2">
        <label className="text-sm text-ink-muted">
          작물
          <select
            value={cropId}
            onChange={(e) => setCropId(e.target.value)}
            className="mt-1 w-full rounded border border-line bg-paper px-2 py-1.5 text-ink"
          >
            {crops.map((crop) => (
              <option key={crop.id} value={crop.id}>
                {crop.name}
              </option>
            ))}
          </select>
        </label>

        <label className="text-sm text-ink-muted">
          등급
          <select
            value={grade}
            onChange={(e) => setGrade(e.target.value)}
            className="mt-1 w-full rounded border border-line bg-paper px-2 py-1.5 text-ink"
          >
            {GRADES.map((g) => (
              <option key={g} value={g}>
                {g}
              </option>
            ))}
          </select>
        </label>

        <label className="text-sm text-ink-muted">
          예상 수확량(kg)
          <input
            type="number"
            min="0"
            value={yieldKg}
            onChange={(e) => setYieldKg(e.target.value)}
            className="mt-1 w-full rounded border border-line bg-paper px-2 py-1.5 text-ink"
          />
        </label>

        <label className="text-sm text-ink-muted">
          출하 예정일
          <input
            type="date"
            value={date}
            onChange={(e) => setDate(e.target.value)}
            className="mt-1 w-full rounded border border-line bg-paper px-2 py-1.5 text-ink"
          />
        </label>

        <label className="text-sm text-ink-muted sm:col-span-2">
          지역 (선택)
          <input
            type="text"
            value={region}
            onChange={(e) => setRegion(e.target.value)}
            placeholder="예: 충남 논산시"
            className="mt-1 w-full rounded border border-line bg-paper px-2 py-1.5 text-ink placeholder:text-ink-faint"
          />
        </label>
      </div>

      {error && <p className="mt-2 text-sm text-status-bad">{error}</p>}

      <div className="mt-3 flex gap-2">
        <button
          type="submit"
          disabled={submitting}
          className="rounded bg-forest px-3 py-1.5 text-sm font-medium text-paper-raised transition-colors hover:bg-forest-deep disabled:opacity-50"
        >
          {submitting ? "등록 중..." : "등록"}
        </button>
        <button
          type="button"
          onClick={onCancel}
          className="rounded border border-line px-3 py-1.5 text-sm text-ink-muted hover:text-ink"
        >
          취소
        </button>
      </div>
    </form>
  )
}
