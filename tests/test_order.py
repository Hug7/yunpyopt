"""Tests for yunpyopt.domain.schema.order."""

from __future__ import annotations

from yunpyopt.domain.schema.order import (
    CargoOrder,
    CargoSubOrder,
    CargoSubOrderDimensionValue,
    CargoSubOrderLabelValue,
)


class TestCargoOrder:
    def test_construct_minimal(self) -> None:
        co = CargoOrder(
            code="ORD001",
            pick_location_code="WH001",
            drop_location_code="WH002",
            earliest_pick_datetime="2025-01-01 08:00",
            latest_pick_datetime="2025-01-01 12:00",
            earliest_drop_datetime="2025-01-01 14:00",
            latest_drop_datetime="2025-01-01 18:00",
        )
        assert co.code == "ORD001"
        assert co.name is None


class TestCargoSubOrder:
    def test_construct(self) -> None:
        cso = CargoSubOrder(
            cargo_order_code="ORD001",
            cargo_sub_order_code="SUB001",
            quantity=10,
        )
        assert cso.quantity == 10
        assert cso.cargo_sub_order_name is None


class TestCargoSubOrderDimensionValue:
    def test_construct(self) -> None:
        csodv = CargoSubOrderDimensionValue(
            cargo_order_code="ORD001",
            cargo_sub_order_code="SUB001",
            dimension_code="WEIGHT",
            dimension_value=100.5,
        )
        assert csodv.dimension_value == 100.5


class TestCargoSubOrderLabelValue:
    def test_construct(self) -> None:
        csolv = CargoSubOrderLabelValue(
            cargo_order_code="ORD001",
            cargo_sub_order_code="SUB001",
            label_code="FRAGILE",
            label_value="YES",
        )
        assert csolv.label_value == "YES"
