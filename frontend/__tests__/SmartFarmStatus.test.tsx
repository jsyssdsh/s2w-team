import { render, screen } from "@testing-library/react"
import SmartFarmStatus from "@/components/SmartFarmStatus"
import type { SensorEvaluation, SensorMetric } from "@/lib/types"

function evaluation(overrides: Partial<SensorEvaluation> = {}): SensorEvaluation {
  return {
    metric: "temperature",
    value: 25,
    min_value: 22,
    max_value: 27,
    status: "정상",
    control_action: null,
    ...overrides,
  }
}

describe("SmartFarmStatus", () => {
  it("shows a waiting message when there are no readings yet", () => {
    render(<SmartFarmStatus readings={{}} connectionStatus="connecting" />)
    expect(screen.getByText("센서 데이터를 기다리는 중입니다")).toBeInTheDocument()
  })

  it("renders temperature, humidity, soil moisture and light readings", () => {
    const readings: Partial<Record<SensorMetric, SensorEvaluation>> = {
      temperature: evaluation({ metric: "temperature", value: 25 }),
      humidity: evaluation({ metric: "humidity", value: 68, status: "정상" }),
      soil_moisture: evaluation({ metric: "soil_moisture", value: 41, status: "정상", control_action: "급수 후 41%" }),
      light: evaluation({ metric: "light", value: 101, status: "정상" }),
    }
    render(<SmartFarmStatus readings={readings} connectionStatus="connected" />)
    expect(screen.getByText("25.0°C")).toBeInTheDocument()
    expect(screen.getByText("68%")).toBeInTheDocument()
    expect(screen.getByText("41%")).toBeInTheDocument()
    expect(screen.getByText("101%")).toBeInTheDocument()
    expect(screen.getByText("급수 후 41%")).toBeInTheDocument()
  })

  it("flags an out-of-range reading using the backend's own evaluation", () => {
    const readings: Partial<Record<SensorMetric, SensorEvaluation>> = {
      temperature: evaluation({ metric: "temperature", value: 29.4, status: "기준초과", control_action: "환기 후 26.5℃" }),
    }
    render(<SmartFarmStatus readings={readings} connectionStatus="connected" />)
    expect(screen.getByText("29.4°C")).toHaveClass("text-status-bad")
    expect(screen.getByText("환기 후 26.5℃")).toBeInTheDocument()
  })

  it("shows the disconnected label while reconnecting", () => {
    render(<SmartFarmStatus readings={{}} connectionStatus="disconnected" />)
    expect(screen.getByText("연결 끊김 - 재시도 중")).toBeInTheDocument()
  })
})
