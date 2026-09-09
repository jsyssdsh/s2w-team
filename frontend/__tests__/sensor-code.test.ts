import { makeSensorCode, parseSensorCode } from "@/lib/sensor-code"

describe("makeSensorCode", () => {
  it("joins the smart farm id and metric with a colon", () => {
    expect(makeSensorCode("smart-farm-tomato", "temperature")).toBe("smart-farm-tomato:temperature")
  })
})

describe("parseSensorCode", () => {
  it("splits on the last colon", () => {
    expect(parseSensorCode("smart-farm-tomato:temperature")).toEqual({
      smartFarmId: "smart-farm-tomato",
      metric: "temperature",
    })
  })

  it("returns null for a code with no colon", () => {
    expect(parseSensorCode("토마토")).toBeNull()
  })
})
