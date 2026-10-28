"""承运商 — Carrier, CarrierLabelValue, Vehicle."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .table import Table


@dataclass
class Carrier(Table):
    """承运商。

    Attributes:
        code: 承运商编码，唯一标识。
        name: 承运商名称。
    """

    code: str
    name: str | None = None

    def __repr__(self) -> str:
        cls = type(self).__name__
        return f"{cls}(code={self.code!r}, name={self.name!r})"

    def to_dict(self) -> dict[str, Any]:
        return {
            "Code": self.code,
            "Name": self.name if self.name is not None else "",
        }

    @staticmethod
    def empty_dict() -> dict[str, Any]:
        return {
            "Code": "",
            "Name": "",
        }

    @staticmethod
    def table_name() -> str:
        return "Carrier"

    def __lt__(self, other) -> bool:
        if not isinstance(other, Carrier):
            return False

        return self.code < other.code


@dataclass
class CarrierLabelValue:
    """承运商标签值。

    主键: (carrier_code, label_code)。

    Attributes:
        carrier_code: 承运商编码，引用 Carrier.code。
        label_code: 标签编码，引用 Label.code 且 LabelApply.apply_item='Carrier'。
        label_value: 标签取值，引用 LabelValue(label_code, label_value)。
    """

    carrier_code: str
    label_code: str
    label_value: str

    def __repr__(self) -> str:
        cls = type(self).__name__
        return (
            f"{cls}(carrier_code={self.carrier_code!r}, "
            f"label_code={self.label_code!r}, "
            f"label_value={self.label_value!r})"
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "CarrierCode": self.carrier_code,
            "LabelCode": self.label_code,
            "LabelValue": self.label_value,
        }

    @staticmethod
    def empty_dict() -> dict[str, Any]:
        return {
            "CarrierCode": "",
            "LabelCode": "",
            "LabelValue": "",
        }

    @staticmethod
    def columns() -> list[str]:
        return ["CarrierCode", "LabelCode", "LabelValue"]

    @staticmethod
    def table_name() -> str:
        return "CarrierLabelValue"

    def __eq__(self, o) -> bool:
        if not isinstance(o, CarrierLabelValue):
            return False
        if self.carrier_code != o.carrier_code:
            return False
        if self.label_code != o.label_code:
            return False
        if self.label_value != o.label_value:
            return False
        return True

    def __hash__(self):
        return hash((self.carrier_code, self.label_code, self.label_value))

    def __lt__(self, other):
        if not isinstance(other, CarrierLabelValue):
            return False

        return (self.carrier_code, self.label_code, self.label_value) < (
            other.carrier_code,
            other.label_code,
            other.label_value,
        )


@dataclass
class Vehicle:
    """车辆。

    主键: (carrier_code, vehicle_model_code)。

    Attributes:
        carrier_code: 承运商编码，引用 Carrier.code。
        vehicle_model_code: 车型编码，引用 VehicleModel.code。
        count: 车辆数量。
        origin_location_code: 起始站点编码，不为空时引用 Location.code。
        destination_location_code: 目标站点编码，不为空时引用 Location.code。
    """

    carrier_code: str
    vehicle_model_code: str
    count: int
    origin_location_code: str | None = None
    destination_location_code: str | None = None

    def __repr__(self) -> str:
        cls = type(self).__name__
        return (
            f"{cls}(carrier_code={self.carrier_code!r}, "
            f"vehicle_model_code={self.vehicle_model_code!r}, "
            f"count={self.count})"
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "CarrierCode": self.carrier_code,
            "VehicleModelCode": self.vehicle_model_code,
            "Count": self.count,
            "OriginLocationCode": self.get_origin_location_code(),
            "DestinationLocationCode": self.get_destination_location_code(),
        }

    @staticmethod
    def empty_dict() -> dict[str, Any]:
        return {
            "CarrierCode": "",
            "VehicleModelCode": "",
            "Count": "",
            "OriginLocationCode": "",
            "DestinationLocationCode": "",
        }

    @staticmethod
    def table_name() -> str:
        return "Vehicle"

    def get_origin_location_code(self) -> str:
        return self.origin_location_code if self.origin_location_code is not None else ""

    def get_destination_location_code(self) -> str:
        return self.destination_location_code if self.destination_location_code is not None else ""

    def __eq__(self, o) -> bool:
        if not isinstance(o, Vehicle):
            return False
        if self.carrier_code != o.carrier_code:
            return False
        if self.vehicle_model_code != o.vehicle_model_code:
            return False
        if self.get_origin_location_code() != o.get_origin_location_code():
            return False
        if self.get_destination_location_code() != o.get_destination_location_code():
            return False
        return True

    def __hash__(self):
        return hash(
            (
                self.carrier_code,
                self.vehicle_model_code,
                self.get_origin_location_code(),
                self.get_destination_location_code(),
            )
        )

    def __lt__(self, other) -> bool:
        if not isinstance(other, Vehicle):
            return False

        return (self.carrier_code, self.vehicle_model_code) < (other.carrier_code, other.vehicle_model_code)
