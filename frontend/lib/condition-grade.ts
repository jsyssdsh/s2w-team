import type { ConditionGrade } from "./types"

// Shared with StatusBadge and IdleLandMap so a plot's status reads the same
// wherever it appears. "상태 개선필요" doesn't read naturally in Korean --
// SPEC 4.4 itself labels that case "개선 필요" without the "상태" prefix.
const LABEL: Record<ConditionGrade, string> = {
  최상: "상태 최상",
  양호: "상태 양호",
  개선필요: "개선 필요",
}

export function conditionGradeLabel(grade: ConditionGrade): string {
  return LABEL[grade]
}
