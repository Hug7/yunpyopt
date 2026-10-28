"""订单 — CargoOrder, CargoSubOrder, CargoSubOrderDimensionValue, CargoSubOrderLabelValue."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .table import Table


@dataclass
class CargoOrder(Table):
    """订单。

    Attributes:
        code: 订单编码，唯一标识。
        name: 订单名称。
        pick_location_code: 提货站点编码，引用 Location.code。
        drop_location_code: 卸货站点编码，引用 Location.code。
        earliest_pick_datetime: 最早提货时间，格式 "%Y-%m-%d %H:%M"。
        latest_pick_datetime: 最晚提货时间，格式 "%Y-%m-%d %H:%M"。
        earliest_drop_datetime: 最早卸货时间，格式 "%Y-%m-%d %H:%M"。
        latest_drop_datetime: 最晚卸货时间，格式 "%Y-%m-%d %H:%M"。
    """

    code: str
    pick_location_code: str
    drop_location_code: str
    earliest_pick_datetime: str
    latest_pick_datetime: str
    earliest_drop_datetime: str
    latest_drop_datetime: str
    name: str | None = None

    def __repr__(self) -> str:
        cls = type(self).__name__
        return f"{cls}(code={self.code!r}, name={self.name!r})"

    def to_dict(self) -> dict[str, Any]:
        return {
            "Code": self.code,
            "Name": self.name if self.name is not None else "",
            "PickLocationCode": self.pick_location_code,
            "DropLocationCode": self.drop_location_code,
            "EarliestPickDateTime": self.earliest_pick_datetime,
            "LatestPickDateTime": self.latest_pick_datetime,
            "EarliestDropDateTime": self.earliest_drop_datetime,
            "LatestDropDateTime": self.latest_drop_datetime,
        }

    @staticmethod
    def empty_dict() -> dict[str, Any]:
        return {
            "Code": "",
            "Name": "",
            "PickLocationCode": "",
            "DropLocationCode": "",
            "EarliestPickDateTime": "",
            "LatestPickDateTime": "",
            'EarliestDropDateTime": "",LatestDropDateTime': "",
        }

    @staticmethod
    def table_name() -> str:
        return "CargoOrder"

    def __lt__(self, other):
        if not isinstance(other, CargoOrder):
            return False

        return self.code < other.code


@dataclass
class CargoSubOrder(Table):
    """子订单。

    主键: (cargo_order_code, cargo_sub_order_code)。

    Attributes:
        cargo_order_code: 父订单编码，引用 CargoOrder.code。
        cargo_sub_order_code: 子订单编码，同一父订单下唯一。
        quantity: 货量。
        cargo_sub_order_name: 子订单名称。
    """

    cargo_order_code: str
    cargo_sub_order_code: str
    quantity: int
    cargo_sub_order_name: str | None = None

    def __repr__(self) -> str:
        cls = type(self).__name__
        return f"{cls}(cargo_order_code={self.cargo_order_code!r}, cargo_sub_order_code={self.cargo_sub_order_code!r})"

    def to_dict(self) -> dict[str, Any]:
        return {
            "CargoOrderCode": self.cargo_order_code,
            "CargoSubOrderCode": self.cargo_sub_order_code,
            "CargoSubOrderName": self.cargo_sub_order_name if self.cargo_sub_order_name is not None else "",
            "Quantity": self.quantity,
        }

    @staticmethod
    def empty_dict() -> dict[str, Any]:
        return {
            "CargoOrderCode": "",
            "CargoSubOrderCode": "",
            "CargoSubOrderName": "",
            "Quantity": "",
        }

    @staticmethod
    def table_name() -> str:
        return "CargoSubOrder"

    def __lt__(self, other):
        if not isinstance(other, CargoSubOrder):
            return False

        return (self.cargo_order_code, self.cargo_sub_order_code) < (other.cargo_order_code, other.cargo_sub_order_code)


@dataclass
class CargoSubOrderDimensionValue(Table):
    """子订单维度值。

    主键: (cargo_order_code, cargo_sub_order_code, dimension_code)。

    Attributes:
        cargo_order_code: 父订单编码，联合关联 CargoSubOrder。
        cargo_sub_order_code: 子订单编码，联合关联 CargoSubOrder。
        dimension_code: 维度编码，引用 Dimension.code。
        dimension_value: 维度值。
    """

    cargo_order_code: str
    cargo_sub_order_code: str
    dimension_code: str
    dimension_value: float

    def __repr__(self) -> str:
        cls = type(self).__name__
        return (
            f"{cls}(cargo_order_code={self.cargo_order_code!r}, "
            f"cargo_sub_order_code={self.cargo_sub_order_code!r}, "
            f"dimension_code={self.dimension_code!r})"
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "CargoOrderCode": self.cargo_order_code,
            "CargoSubOrderCode": self.cargo_sub_order_code,
            "DimensionCode": self.dimension_code,
            "DimensionValue": self.dimension_value,
        }

    @staticmethod
    def empty_dict() -> dict[str, Any]:
        return {
            "CargoOrderCode": "",
            "CargoSubOrderCode": "",
            "DimensionCode": "",
            "DimensionValue": "",
        }

    @staticmethod
    def columns() -> list[str]:
        return ["CargoOrderCode", "CargoSubOrderCode", "DimensionCode", "DimensionValue"]

    @staticmethod
    def table_name() -> str:
        return "CargoSubOrderDimensionValue"

    def __eq__(self, o: object) -> bool:
        if not isinstance(o, CargoSubOrderDimensionValue):
            return False
        if self.cargo_order_code != o.cargo_order_code:
            return False
        if self.cargo_sub_order_code != o.cargo_sub_order_code:
            return False
        if self.dimension_code != o.dimension_code:
            return False
        return True

    def __hash__(self):
        return hash((self.cargo_order_code, self.cargo_sub_order_code, self.dimension_code))

    def __lt__(self, other):
        if not isinstance(other, CargoSubOrderDimensionValue):
            return False

        return (self.cargo_order_code, self.cargo_sub_order_code, self.dimension_code) < (
            other.cargo_order_code,
            other.cargo_sub_order_code,
            other.dimension_code,
        )


@dataclass
class CargoSubOrderLabelValue(Table):
    """子订单标签值。

    主键: (cargo_order_code, cargo_sub_order_code, label_code)。

    Attributes:
        cargo_order_code: 父订单编码，联合关联 CargoSubOrder。
        cargo_sub_order_code: 子订单编码，联合关联 CargoSubOrder。
        label_code: 标签编码，引用 Label.code 且 LabelApply.apply_item='Order'。
        label_value: 标签取值，引用 LabelValue(label_code, label_value)。
    """

    cargo_order_code: str
    cargo_sub_order_code: str
    label_code: str
    label_value: str

    def __repr__(self) -> str:
        cls = type(self).__name__
        return (
            f"{cls}(cargo_order_code={self.cargo_order_code!r}, "
            f"cargo_sub_order_code={self.cargo_sub_order_code!r}, "
            f"label_code={self.label_code!r}, "
            f"label_value={self.label_value!r})"
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "CargoOrderCode": self.cargo_order_code,
            "CargoSubOrderCode": self.cargo_sub_order_code,
            "LabelCode": self.label_code,
            "LabelValue": self.label_value,
        }

    @staticmethod
    def empty_dict() -> dict[str, Any]:
        return {
            "CargoOrderCode": "",
            "CargoSubOrderCode": "",
            "LabelCode": "",
            "LabelValue": "",
        }

    @staticmethod
    def columns() -> list[str]:
        return ["CargoOrderCode", "CargoSubOrderCode", "LabelCode", "LabelValue"]

    @staticmethod
    def table_name() -> str:
        return "CargoSubOrderLabelValue"

    def __eq__(self, o: object) -> bool:
        if not isinstance(o, CargoSubOrderLabelValue):
            return False
        if self.cargo_order_code != o.cargo_order_code:
            return False
        if self.cargo_sub_order_code != o.cargo_sub_order_code:
            return False
        if self.label_code != o.label_code:
            return False
        if self.label_value != o.label_value:
            return False
        return True

    def __hash__(self):
        return hash((self.cargo_order_code, self.cargo_sub_order_code, self.label_code, self.label_value))

    def __lt__(self, other):
        if not isinstance(other, CargoSubOrderLabelValue):
            return False

        return (self.cargo_order_code, self.cargo_sub_order_code, self.label_code, self.label_value) < (
            other.cargo_order_code,
            other.cargo_sub_order_code,
            other.label_code,
            other.label_value,
        )
