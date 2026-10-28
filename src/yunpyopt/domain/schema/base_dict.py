"""基础字典 — Dimension, Label, LabelValue, LabelApply."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from typing_extensions import override

from .table import Table


@dataclass
class Dimension(Table):
    """计算维度。

    Attributes:
        code: 维度编码，唯一标识。
        name: 维度名称。
        precision: 精度，0=整数，1=小数点后1位... [0, 4]。
    """

    code: str
    precision: int
    name: str | None = None

    def __repr__(self) -> str:
        cls = type(self).__name__
        return f"{cls}(code={self.code!r}, precision={self.precision})"

    @override
    def to_dict(self) -> dict[str, Any]:
        return {
            "Code": self.code,
            "Precision": self.precision,
            "Name": self.name if self.name is not None else "",
        }

    @staticmethod
    def empty_dict() -> dict[str, Any]:
        return {
            "Code": "",
            "Precision": "",
            "Name": "",
        }

    @staticmethod
    def table_name() -> str:
        return "Dimension"

    def __lt__(self, other):
        if not isinstance(other, Dimension):
            return False

        return self.code < other.code


@dataclass
class Label(Table):
    """标签集合。

    Attributes:
        code: 标签编码，唯一标识。
        name: 标签名称。
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
    def columns() -> list[str]:
        return ["Code", "Name"]

    @staticmethod
    def table_name() -> str:
        return "Label"

    def __lt__(self, other):
        if not isinstance(other, Label):
            return False

        return self.code < other.code


@dataclass
class LabelValue(Table):
    """标签可选值。

    主键: (label_code, label_value)。

    Attributes:
        label_code: 标签编码，引用 Label.code。
        label_value: 标签取值。
    """

    label_code: str
    label_value: str

    def __repr__(self) -> str:
        cls = type(self).__name__
        return f"{cls}(label_code={self.label_code!r}, label_value={self.label_value!r})"

    def to_dict(self) -> dict[str, Any]:
        return {
            "LabelCode": self.label_code,
            "LabelValue": self.label_value,
        }

    @staticmethod
    def empty_dict() -> dict[str, Any]:
        return {
            "LabelCode": "",
            "LabelValue": "",
        }

    @staticmethod
    def columns() -> list[str]:
        return ["LabelCode", "LabelValue"]

    @staticmethod
    def table_name() -> str:
        return "LabelValue"

    def __lt__(self, other):
        if not isinstance(other, LabelValue):
            return False

        return (self.label_code, self.label_value) < (other.label_code, other.label_value)


class LabelApplyItem:
    LOCATION: str = "Location"
    VEHICLE_MODEL: str = "VehicleModel"
    ORDER: str = "Order"
    CARRIER: str = "Carrier"


LabelApplyItemSet: set[str] = {
    LabelApplyItem.LOCATION,
    LabelApplyItem.VEHICLE_MODEL,
    LabelApplyItem.ORDER,
    LabelApplyItem.CARRIER,
}


class LabelApply(Table):
    """标签和实体的映射。

    主键: (label_code, apply_item)。

    Attributes:
        label_code: 标签编码，引用 Label.code。
        apply_item: 适用实体类型 (Location / VehicleModel / Order / Carrier)。 参考LabelApplyItem的成员变量
    """

    label_code: str
    apply_item: str

    def __init__(self, label_code: str, apply_item: str):
        self.label_code = label_code
        self.apply_item = apply_item
        if not LabelApplyItemSet.__contains__(apply_item):
            raise ValueError(f"apply_item={apply_item!r} not in LabelApplyItems")

    def __repr__(self) -> str:
        cls = type(self).__name__
        return f"{cls}(label_code={self.label_code!r}, apply_item={self.apply_item!r})"

    def to_dict(self) -> dict[str, Any]:
        return {
            "LabelCode": self.label_code,
            "ApplyItem": self.apply_item,
        }

    @staticmethod
    def empty_dict() -> dict[str, Any]:
        return {
            "LabelCode": "",
            "ApplyItem": "",
        }

    @staticmethod
    def columns() -> list[str]:
        return ["LabelCode", "ApplyItem"]

    @staticmethod
    def table_name() -> str:
        return "LabelApply"

    def __lt__(self, other):
        if not isinstance(other, LabelApplyItem):
            return False

        return (self.label_code, self.apply_item) < (self.label_code, self.apply_item)
