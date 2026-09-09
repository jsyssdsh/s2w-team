"""Tests against SPEC 5.3's 1,700kg tomato grade-based retailer matching table."""

import pytest

from app.services.buyer_matching import ShipmentLot, match_lots_to_retailer_types


def _spec_lots() -> list[ShipmentLot]:
    return [
        ShipmentLot("shipment-premium", "특상품", 300),
        ShipmentLot("shipment-standard", "상품", 700),
        ShipmentLot("shipment-offgrade", "규격외", 500),
        ShipmentLot("shipment-urgent", "판매기한임박", 200),
    ]


class TestMatchLotsToRetailerTypes:
    def test_matches_spec_table(self):
        matches = {m.shipment_plan_id: m for m in match_lots_to_retailer_types(_spec_lots())}
        assert matches["shipment-premium"].recommended_retailer_type == "대형마트"
        assert matches["shipment-standard"].recommended_retailer_type == "학교급식"
        assert matches["shipment-offgrade"].recommended_retailer_type == "가공업체"
        assert matches["shipment-urgent"].recommended_retailer_type == "지역음식점"

    def test_unknown_grade_raises(self):
        with pytest.raises(ValueError):
            match_lots_to_retailer_types([ShipmentLot("x", "존재하지않는등급", 1)])
