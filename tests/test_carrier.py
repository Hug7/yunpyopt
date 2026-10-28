"""Tests for yunpyopt.domain.schema.carrier."""

from __future__ import annotations

from yunpyopt.domain.schema.carrier import Carrier, CarrierLabelValue, Vehicle


class TestCarrier:
    def test_construct_minimal(self) -> None:
        c = Carrier(code="C1")
        assert c.code == "C1"
        assert c.name is None

    def test_construct_full(self) -> None:
        c = Carrier(code="C1", name="Express Logistics")
        assert c.name == "Express Logistics"


class TestCarrierLabelValue:
    def test_construct(self) -> None:
        clv = CarrierLabelValue(carrier_code="C1", label_code="PRIORITY", label_value="HIGH")
        assert clv.carrier_code == "C1"


class TestVehicle:
    def test_construct_minimal(self) -> None:
        v = Vehicle(carrier_code="C1", vehicle_model_code="VM1", count=5)
        assert v.count == 5
        assert v.origin_location_code is None
        assert v.destination_location_code is None

    def test_construct_full(self) -> None:
        v = Vehicle(
            carrier_code="C1",
            vehicle_model_code="VM1",
            count=5,
            origin_location_code="WH001",
            destination_location_code="WH002",
        )
        assert v.origin_location_code == "WH001"
        assert v.destination_location_code == "WH002"
