import { conditionGradeLabel } from "@/lib/condition-grade"

describe("conditionGradeLabel", () => {
  it("prefixes 최상 and 양호 with 상태", () => {
    expect(conditionGradeLabel("최상")).toBe("상태 최상")
    expect(conditionGradeLabel("양호")).toBe("상태 양호")
  })

  it("renders 개선필요 as 개선 필요 without the 상태 prefix", () => {
    expect(conditionGradeLabel("개선필요")).toBe("개선 필요")
  })
})
