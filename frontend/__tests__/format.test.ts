import { formatDate, formatKg, formatKrw, formatPercent, formatPyeong, formatTime } from "@/lib/format"

describe("formatKrw", () => {
  it("formats positive values as KRW with no decimals", () => {
    expect(formatKrw(10000)).toBe("₩10,000")
  })

  it("formats zero", () => {
    expect(formatKrw(0)).toBe("₩0")
  })

  it("formats large values with commas", () => {
    expect(formatKrw(1234567)).toBe("₩1,234,567")
  })
})

describe("formatPercent", () => {
  it("formats positive percent with plus sign", () => {
    expect(formatPercent(2.5)).toBe("+2.5%")
  })

  it("formats negative percent with minus sign", () => {
    expect(formatPercent(-1.23)).toBe("-1.2%")
  })

  it("formats zero percent with plus sign", () => {
    expect(formatPercent(0)).toBe("+0.0%")
  })
})

describe("formatKg", () => {
  it("appends kg suffix with thousands separators", () => {
    expect(formatKg(1000)).toBe("1,000kg")
  })
})

describe("formatPyeong", () => {
  it("appends 평 suffix", () => {
    expect(formatPyeong(900)).toBe("900평")
  })
})

describe("formatDate", () => {
  it("formats an ISO date as Korean month/day", () => {
    expect(formatDate("2026-08-10T00:00:00Z")).toContain("8")
  })

  it("returns the original string for an invalid date", () => {
    expect(formatDate("not-a-date")).toBe("not-a-date")
  })
})

describe("formatTime", () => {
  it("returns the original string for an invalid time", () => {
    expect(formatTime("not-a-date")).toBe("not-a-date")
  })
})
