"""Tests against SPEC 5.4's onion oversupply example."""

from app.services.supply_risk import compute_supply_risk


class TestComputeSupplyRisk:
    def test_matches_spec_onion_scenario(self):
        result = compute_supply_risk(
            farmer_planned_kg=120_000, wholesaler_inventory_kg=8_000, retailer_demand_kg=100_000
        )
        assert result.total_supply_ton == 128.0
        assert result.excess_supply_ton == 28.0
        assert result.risk_level == "위험"

    def test_mitigation_plan_matches_spec_allocation(self):
        result = compute_supply_risk(
            farmer_planned_kg=120_000, wholesaler_inventory_kg=8_000, retailer_demand_kg=100_000
        )
        plan = {a.channel: a.processed_volume_ton for a in result.response_plan}
        assert plan["식품가공업체 추가 연결"] == 12.0
        assert plan["학교급식 업체 추가 연결"] == 6.0
        assert plan["출하 시기 조정"] == 7.0
        assert plan["지역 공동판매 연계"] == 3.0
        assert round(sum(plan.values()), 1) == result.excess_supply_ton

    def test_supply_within_demand_is_safe(self):
        result = compute_supply_risk(
            farmer_planned_kg=50_000, wholesaler_inventory_kg=0, retailer_demand_kg=100_000
        )
        assert result.risk_level == "안전"
        assert result.response_plan == []

    def test_mild_excess_is_caution(self):
        # 15% over demand -> above the 10% caution threshold, below 20% danger.
        result = compute_supply_risk(
            farmer_planned_kg=115_000, wholesaler_inventory_kg=0, retailer_demand_kg=100_000
        )
        assert result.risk_level == "주의"
