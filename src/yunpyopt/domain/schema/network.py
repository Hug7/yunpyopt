"""路由网络 — DistMatrix."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .table import Table


@dataclass
class DistMatrixCode(Table):
    """距离矩阵编码。

    主键: (code)。

    Attributes:
        code: 距离矩阵编码。
        name: 距离矩阵编码名称。
    """

    code: str
    name: str | None = None

    def __repr__(self) -> str:
        cls = type(self).__name__
        return f"{cls}(code={self.code}, to={self.name}"

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
        return "DistMatrixCode"


@dataclass
class DistMatrix(Table):
    """距离矩阵。

    主键: (from_location_code, to_location_code, dist_matrix_code)。

    Attributes:
        from_location_code: 起始站点编码，引用 Location.code。
        to_location_code: 目标站点编码，引用 Location.code。
        dist_matrix_code: 距离矩阵编码 必须存在于 DistMatrixCode.code
        distance: 距离（米），[0, 60000000]。
        time: 耗时（秒），[0, 2160000000]。
    """

    from_location_code: str
    to_location_code: str
    dist_matrix_code: str
    distance: int
    time: int

    def __repr__(self) -> str:
        cls = type(self).__name__
        return f"{cls}(from={self.from_location_code!r}, to={self.to_location_code!r}, matrix={self.dist_matrix_code})"

    def to_dict(self) -> dict[str, Any]:
        return {
            "FromLocationCode": self.from_location_code,
            "ToLocationCode": self.to_location_code,
            "DistMatrixCode": self.dist_matrix_code,
            "Distance": self.distance,
            "Time": self.time,
        }

    @staticmethod
    def empty_dict() -> dict[str, Any]:
        return {"FromLocationCode": "", "ToLocationCode": "", "DistMatrixCode": "", "Distance": "", "Time": ""}

    @staticmethod
    def table_name() -> str:
        return "DistMatrix"
