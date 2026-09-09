"""Tests against SPEC 5.5's tomato sensor auto-control example."""

from app.services.sensors import evaluate_latest_readings, evaluate_sensor_reading


class TestEvaluateSensorReading:
    def test_temperature_above_range_triggers_ventilation(self):
        # SPEC 5.5: 22~27C range, 29.4C reading -> 환기 후 26.5C
        result = evaluate_sensor_reading("temperature", 29.4, 22, 27)
        assert result.status == "기준초과"
        assert result.control_action == "환기 작동"

    def test_humidity_within_range_needs_no_action(self):
        # SPEC 5.5: 60~75% range, 68% reading -> 정상 상태 유지
        result = evaluate_sensor_reading("humidity", 68, 60, 75)
        assert result.status == "정상"
        assert result.control_action is None

    def test_soil_moisture_below_range_triggers_pump(self):
        # SPEC 5.5: 35~55% range, 28% reading -> 급수 후 41%
        result = evaluate_sensor_reading("soil_moisture", 28, 35, 55)
        assert result.status == "기준미달"
        assert result.control_action == "워터펌프 급수 시작"

    def test_light_below_floor_triggers_lighting_with_no_ceiling(self):
        # SPEC 5.5: floor-only range (기준의 82% -> 101% after lighting).
        result = evaluate_sensor_reading("light", 16400, 20000, None)
        assert result.status == "기준미달"
        assert result.control_action == "조명 작동"

        result_after = evaluate_sensor_reading("light", 20200, 20000, None)
        assert result_after.status == "정상"
        assert result_after.control_action is None

    def test_evaluate_latest_readings_skips_metrics_without_a_range(self):
        readings = {"temperature": 29.4, "unknown_metric": 1.0}
        ranges = {"temperature": (22.0, 27.0)}
        results = evaluate_latest_readings(readings, ranges)
        assert len(results) == 1
        assert results[0].metric == "temperature"
