"""车型 — VehicleModel, VehicleModelDimensionValue, VehicleModelLabelValue."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .table import Table


@dataclass
class VehicleModel(Table):
    """车型定义。

    Attributes:
        code: 车型编码，唯一标识。
        name: 车型名称。
        dist_matrix_code: 距离矩阵编码，必须存在于 DistMatrixCode.code。
    """

    code: str
    dist_matrix_code: str
    name: str | None = None

    def __repr__(self) -> str:
        cls = type(self).__name__
        return f"{cls}(code={self.code!r}, name={self.name!r})"

    def to_dict(self) -> dict[str, Any]:
        return {
            "Code": self.code,
            "Name": self.name if self.name is not None else "",
            "DistMatrixCode": self.dist_matrix_code,
        }

    @staticmethod
    def empty_dict() -> dict[str, Any]:
        return {
            "Code": "",
            "Name": "",
            "DistMatrixCode": "",
        }

    @staticmethod
    def table_name() -> str:
        return "VehicleModel"

    def __lt__(self, other):
        if not isinstance(other, VehicleModel):
            return False

        return self.code < other.code


@dataclass
class VehicleModelDimensionValue:
    """车型维度值。

    主键: (vehicle_model_code, dimension_code)。

    Attributes:
        vehicle_model_code: 车型编码，引用 VehicleModel.code。
        dimension_code: 维度编码，引用 Dimension.code。
        dimension_value: 维度值。
    """

    vehicle_model_code: str
    dimension_code: str
    dimension_value: float

    def __repr__(self) -> str:
        cls = type(self).__name__
        return f"{cls}(vehicle_model_code={self.vehicle_model_code!r}, dimension_code={self.dimension_code!r})"

    def to_dict(self) -> dict[str, Any]:
        return {
            "VehicleModelCode": self.vehicle_model_code,
            "DimensionCode": self.dimension_code,
            "DimensionValue": self.dimension_value,
        }

    @staticmethod
    def empty_dict() -> dict[str, Any]:
        return {
            "VehicleModelCode": "",
            "DimensionCode": "",
            "DimensionValue": "",
        }

    @staticmethod
    def columns() -> list[str]:
        return ["VehicleModelCode", "DimensionCode", "DimensionValue"]

    @staticmethod
    def table_name() -> str:
        return "VehicleModelDimensionValue"

    def __eq__(self, o) -> bool:
        if not isinstance(o, VehicleModelDimensionValue):
            return False
        if self.vehicle_model_code != o.vehicle_model_code:
            return False
        if self.dimension_code != o.dimension_code:
            return False
        return True

    def __hash__(self):
        return hash((self.vehicle_model_code, self.dimension_code))

    def __lt__(self, other):
        if not isinstance(other, VehicleModelDimensionValue):
            return False
        return (self.vehicle_model_code, self.dimension_code) < (other.vehicle_model_code, other.dimension_code)


@dataclass
class VehicleModelLabelValue:
    """车型标签值。

    主键: (vehicle_model_code, label_code)。

    Attributes:
        vehicle_model_code: 车型编码，引用 VehicleModel.code。
        label_code: 标签编码，引用 Label.code 且 LabelApply.apply_item='VehicleModel'。
        label_value: 标签取值，引用 LabelValue(label_code, label_value)。
    """

    vehicle_model_code: str
    label_code: str
    label_value: str

    def __repr__(self) -> str:
        cls = type(self).__name__
        return (
            f"{cls}(vehicle_model_code={self.vehicle_model_code!r}, "
            f"label_code={self.label_code!r}, "
            f"label_value={self.label_value!r})"
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "VehicleModelCode": self.vehicle_model_code,
            "LabelCode": self.label_code,
            "LabelValue": self.label_value,
        }

    @staticmethod
    def empty_dict() -> dict[str, Any]:
        return {
            "VehicleModelCode": "",
            "LabelCode": "",
            "LabelValue": "",
        }

    @staticmethod
    def columns() -> list[str]:
        return ["VehicleModelCode", "LabelCode", "LabelValue"]

    @staticmethod
    def table_name() -> str:
        return "VehicleModelLabelValue"

    def __eq__(self, o) -> bool:
        if not isinstance(o, VehicleModelLabelValue):
            return False
        if self.vehicle_model_code != o.vehicle_model_code:
            return False
        if self.label_code != o.label_code:
            return False
        if self.label_value != o.label_value:
            return False
        return True

    def __hash__(self):
        return hash((self.vehicle_model_code, self.label_code, self.label_value))

    def __lt__(self, other):
        if not isinstance(other, VehicleModelLabelValue):
            return False
        return (self.vehicle_model_code, self.label_code) < (other.vehicle_model_code, other.label_code)
