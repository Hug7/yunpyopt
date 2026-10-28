"""Tests for yunpyopt.domain.schema.vehicle_model."""

from __future__ import annotations

from yunpyopt.domain.schema.vehicle_model import (
    VehicleModel,
    VehicleModelDimensionValue,
    VehicleModelLabelValue,
)


class TestVehicleModel:
    def test_construct_minimal(self) -> None:
        vm = VehicleModel(code="VM1", dist_matrix_code=1)
        assert vm.code == "VM1"
        assert vm.name is None

    def test_construct_full(self) -> None:
        vm = VehicleModel(code="VM1", dist_matrix_code=1, name="Box Truck")
        assert vm.name == "Box Truck"


class TestVehicleModelDimensionValue:
    def test_construct(self) -> None:
        vmdv = VehicleModelDimensionValue(vehicle_model_code="VM1", dimension_code="WEIGHT", dimension_value=2000.0)
        assert vmdv.dimension_value == 2000.0


class TestVehicleModelLabelValue:
    def test_construct(self) -> None:
        vmlv = VehicleModelLabelValue(vehicle_model_code="VM1", label_code="REFRIGERATED", label_value="YES")
        assert vmlv.label_value == "YES"
