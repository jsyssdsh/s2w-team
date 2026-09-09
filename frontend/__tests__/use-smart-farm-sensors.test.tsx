import { renderHook, waitFor, act } from "@testing-library/react"
import { useSmartFarmSensors } from "@/lib/use-smart-farm-sensors"
import { getLatestSensorReadings } from "@/lib/api"

jest.mock("@/lib/api", () => ({
  getLatestSensorReadings: jest.fn(),
}))

class FakeEventSource {
  static instances: FakeEventSource[] = []
  onopen: (() => void) | null = null
  onmessage: ((event: { data: string }) => void) | null = null
  onerror: (() => void) | null = null
  constructor(public url: string) {
    FakeEventSource.instances.push(this)
  }
  close() {}
  emit(data: unknown) {
    this.onmessage?.({ data: JSON.stringify(data) })
  }
}

describe("useSmartFarmSensors", () => {
  beforeEach(() => {
    jest.clearAllMocks()
    FakeEventSource.instances = []
    // @ts-expect-error -- test double for the browser EventSource API
    global.EventSource = FakeEventSource
  })

  it("loads the initial evaluation for each smart farm id", async () => {
    ;(getLatestSensorReadings as jest.Mock).mockResolvedValue([
      { metric: "temperature", value: 25, min_value: 22, max_value: 27, status: "정상", control_action: null },
    ])

    const { result } = renderHook(() => useSmartFarmSensors(["smart-farm-tomato"], "crop-tomato"))

    await waitFor(() => expect(result.current.evaluations["smart-farm-tomato"]?.temperature?.value).toBe(25))
    expect(getLatestSensorReadings).toHaveBeenCalledWith("smart-farm-tomato", "crop-tomato")
  })

  it("re-evaluates a metric as out of range when a live update crosses the threshold", async () => {
    ;(getLatestSensorReadings as jest.Mock).mockResolvedValue([
      { metric: "temperature", value: 25, min_value: 22, max_value: 27, status: "정상", control_action: null },
    ])

    const { result } = renderHook(() => useSmartFarmSensors(["smart-farm-tomato"], "crop-tomato"))
    await waitFor(() => expect(result.current.evaluations["smart-farm-tomato"]?.temperature).toBeDefined())

    const source = FakeEventSource.instances[0]
    act(() => {
      source.emit({
        "smart-farm-tomato:temperature": {
          code: "smart-farm-tomato:temperature",
          price: 29.4,
          previous_price: 25,
          timestamp: 0,
          change: 4.4,
          change_percent: 17.6,
          direction: "up",
        },
      })
    })

    await waitFor(() =>
      expect(result.current.evaluations["smart-farm-tomato"]?.temperature?.status).toBe("기준초과")
    )
    expect(result.current.evaluations["smart-farm-tomato"]?.temperature?.value).toBe(29.4)
  })
})
