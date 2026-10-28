"""站点数据 — Location, 标签值, 可用车辆, 工作日历, 作业参数."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .table import Table


@dataclass
class Location(Table):
    """站点基础信息。

    Attributes:
        code: 站点编码，唯一标识。
        name: 站点名称。
        lng: 经度。
        lat: 纬度。
    """

    code: str
    lng: float
    lat: float
    name: str | None = None

    def __repr__(self) -> str:
        cls = type(self).__name__
        return f"{cls}(code={self.code!r}, name={self.name!r})"

    def to_dict(self) -> dict[str, Any]:
        return {
            "Code": self.code,
            "Name": self.name if self.name is not None else "",
            "Lng": self.lng,
            "Lat": self.lat,
        }

    @staticmethod
    def empty_dict() -> dict[str, Any]:
        return {
            "Code": "",
            "Name": "",
            "Lng": "",
            "Lat": "",
        }

    @staticmethod
    def table_name() -> str:
        return "Location"


@dataclass
class LocationLabelValue:
    """站点标签值。

    主键: (location_code, label_code)。

    Attributes:
        location_code: 站点编码，引用 Location.code。
        label_code: 标签编码，引用 Label.code 且 LabelApply.apply_item='Location'。
        label_value: 标签取值，引用 LabelValue(label_code, label_value)。
    """

    location_code: str
    label_code: str
    label_value: str

    def __repr__(self) -> str:
        cls = type(self).__name__
        return (
            f"{cls}(location_code={self.location_code!r}, "
            f"label_code={self.label_code!r}, "
            f"label_value={self.label_value!r})"
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "LocationCode": self.location_code,
            "LabelCode": self.label_code,
            "LabelValue": self.label_value,
        }

    @staticmethod
    def empty_dict() -> dict[str, Any]:
        return {
            "LocationCode": "",
            "LabelCode": "",
            "LabelValue": "",
        }

    @staticmethod
    def columns() -> list[str]:
        return ["LocationCode", "LabelCode", "LabelValue"]

    @staticmethod
    def table_name() -> str:
        return "LocationLabelValue"

    def __eq__(self, o):
        if not isinstance(o, LocationLabelValue):
            return False
        if self.location_code != o.location_code:
            return False
        if self.label_code != o.label_code:
            return False
        if self.label_value != o.label_value:
            return False
        return True

    def __hash__(self) -> int:
        return hash((self.location_code, self.label_code, self.label_value))


@dataclass
class LocationAvailableVehicle:
    """站点可用车辆。

    主键: (location_code, carrier_code, vehicle_model_code)。

    Attributes:
        location_code: 站点编码，引用 Location.code。
        carrier_code: 承运商编码，引用 Carrier.code。
        vehicle_model_code: 车型编码，引用 VehicleModel.code。
    """

    location_code: str
    carrier_code: str
    vehicle_model_code: str

    def __repr__(self) -> str:
        cls = type(self).__name__
        return (
            f"{cls}(location_code={self.location_code!r}, "
            f"carrier_code={self.carrier_code!r}, "
            f"vehicle_model_code={self.vehicle_model_code!r})"
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "LocationCode": self.location_code,
            "CarrierCode": self.carrier_code,
            "VehicleModelCode": self.vehicle_model_code,
        }

    @staticmethod
    def empty_dict() -> dict[str, Any]:
        return {
            "LocationCode": "",
            "CarrierCode": "",
            "VehicleModelCode": "",
        }

    @staticmethod
    def columns() -> list[str]:
        return ["LocationCode", "CarrierCode", "VehicleModelCode"]

    @staticmethod
    def table_name() -> str:
        return "LocationAvailableVehicle"

    def __eq__(self, o):
        if not isinstance(o, LocationAvailableVehicle):
            return False
        if self.location_code != o.location_code:
            return False
        if self.carrier_code != o.carrier_code:
            return False
        if self.vehicle_model_code != o.vehicle_model_code:
            return False
        return True

    def __hash__(self) -> int:
        return hash((self.location_code, self.carrier_code, self.vehicle_model_code))


@dataclass
class WorkCalendarDaily:
    """工作日历（按天）。

    主键: (location_code, calendar_type)。
    与 WorkCalendarWeekly 互斥。

    Attributes:
        location_code: 站点编码，引用 Location.code。
        calendar_type: 日历类型 (PICK / DROP / RESTRICT)。
        daily: 每天的时间窗列表，格式 "%H%M%H%M;%H%M%H%M"。
    """

    location_code: str
    calendar_type: str
    daily: str

    def __repr__(self) -> str:
        cls = type(self).__name__
        return f"{cls}(location_code={self.location_code!r}, calendar_type={self.calendar_type!r})"

    def to_dict(self) -> dict[str, Any]:
        return {
            "LocationCode": self.location_code,
            "CalendarType": self.calendar_type,
            "Daily": self.daily,
        }

    @staticmethod
    def empty_dict() -> dict[str, Any]:
        return {
            "LocationCode": "",
            "CalendarType": "",
            "Daily": "",
        }

    @staticmethod
    def columns() -> list[str]:
        return ["LocationCode", "CalendarType", "Daily"]

    @staticmethod
    def table_name() -> str:
        return "WorkCalendarDaily"

    def __eq__(self, o):
        if not isinstance(o, WorkCalendarDaily):
            return False
        if self.location_code != o.location_code:
            return False
        if self.calendar_type != o.calendar_type:
            return False
        return True

    def __hash__(self) -> int:
        return hash((self.location_code, self.calendar_type))


@dataclass
class WorkCalendarWeekly:
    """工作日历（按周）。

    主键: (location_code, calendar_type)。
    与 WorkCalendarDaily 互斥。

    Attributes:
        location_code: 站点编码，引用 Location.code。
        calendar_type: 日历类型 (PICK / DROP / RESTRICT)。
        monday: 周一的时间窗列表。
        tuesday: 周二的时间窗列表。
        wednesday: 周三的时间窗列表。
        thursday: 周四的时间窗列表。
        friday: 周五的时间窗列表。
        saturday: 周六的时间窗列表。
        sunday: 周日的时间窗列表。
    """

    location_code: str
    calendar_type: str
    monday: str | None = None
    tuesday: str | None = None
    wednesday: str | None = None
    thursday: str | None = None
    friday: str | None = None
    saturday: str | None = None
    sunday: str | None = None

    def __repr__(self) -> str:
        cls = type(self).__name__
        return f"{cls}(location_code={self.location_code!r}, calendar_type={self.calendar_type!r})"

    def to_dict(self) -> dict[str, Any]:
        return {
            "LocationCode": self.location_code,
            "CalendarType": self.calendar_type,
            "Monday": self.monday if self.monday is not None else "",
            "Tuesday": self.tuesday if self.tuesday is not None else "",
            "Wednesday": self.wednesday if self.wednesday is not None else "",
            "Thursday": self.thursday if self.thursday is not None else "",
            "Friday": self.friday if self.friday is not None else "",
            "Saturday": self.saturday if self.saturday is not None else "",
            "Sunday": self.sunday if self.sunday is not None else "",
        }

    @staticmethod
    def empty_dict() -> dict[str, Any]:
        return {
            "LocationCode": "",
            "CalendarType": "",
            "Monday": "",
            "Tuesday": "",
            "Wednesday": "",
            "Thursday": "",
            "Friday": "",
            "Saturday": "",
            "Sunday": "",
        }

    @staticmethod
    def columns() -> list[str]:
        return [
            "LocationCode",
            "CalendarType",
            "Monday",
            "Tuesday",
            "Wednesday",
            "Thursday",
            "Friday",
            "Saturday",
            "Sunday",
        ]

    @staticmethod
    def table_name() -> str:
        return "WorkCalendarWeekly"

    def __eq__(self, o: object) -> bool:
        if not isinstance(o, WorkCalendarWeekly):
            return False
        if self.location_code != o.location_code:
            return False
        if self.calendar_type != o.calendar_type:
            return False
        return True

    def __hash__(self) -> int:
        return hash((self.location_code, self.calendar_type))


@dataclass
class WorkFixed:
    """站点固定作业时间。

    主键: location_code。

    Attributes:
        location_code: 站点编码，引用 Location.code。
        fixed_pick_time: 固定提货时间（秒），为空时为 0。
        fixed_drop_time: 固定卸货时间（秒），为空时为 0。
    """

    location_code: str
    fixed_pick_time: int | None = None
    fixed_drop_time: int | None = None

    def __repr__(self) -> str:
        cls = type(self).__name__
        return f"{cls}(location_code={self.location_code!r})"

    def to_dict(self) -> dict[str, Any]:
        return {
            "LocationCode": self.location_code,
            "FixedPickTime": self.fixed_pick_time if self.fixed_pick_time is not None else 0,
            "FixedDropTime": self.fixed_drop_time if self.fixed_drop_time is not None else 0,
        }

    @staticmethod
    def empty_dict() -> dict[str, Any]:
        return {
            "LocationCode": "",
            "FixedPickTime": "",
            "FixedDropTime": "",
        }

    @staticmethod
    def columns() -> list[str]:
        return ["LocationCode", "FixedPickTime", "FixedDropTime"]

    @staticmethod
    def table_name() -> str:
        return "WorkFixed"

    def __eq__(self, o: object) -> bool:
        if not isinstance(o, WorkFixed):
            return False
        if self.location_code != o.location_code:
            return False
        return True

    def __hash__(self) -> int:
        return hash(self.location_code)


@dataclass
class WorkEffect:
    """站点作业效率。

    主键: (location_code, dimension_code)。

    Attributes:
        location_code: 站点编码，引用 Location.code。
        activity_type: 动作编码，支持{PICK, DROP}。
        dimension_code: 维度编码，引用 Dimension.code。
        per_hour_process_quantity: 每小时处理量（单位/小时），最大 4 位小数。
    """

    location_code: str
    activity_type: str
    dimension_code: str
    per_hour_process_quantity: float

    def __repr__(self) -> str:
        cls = type(self).__name__
        return (
            f"{cls}(location_code={self.location_code!r}, "
            f"activity_type={self.activity_type!r}, "
            f"dimension_code={self.dimension_code!r})"
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "LocationCode": self.location_code,
            "ActivityType": self.activity_type,
            "DimensionCode": self.dimension_code,
            "PerHourProcessQuantity": self.per_hour_process_quantity,
        }

    @staticmethod
    def empty_dict() -> dict[str, Any]:
        return {
            "LocationCode": "",
            "ActivityType": "",
            "DimensionCode": "",
            "PerHourProcessQuantity": "",
        }

    @staticmethod
    def columns() -> list[str]:
        return ["LocationCode", "ActivityType", "DimensionCode", "PerHourProcessQuantity"]

    @staticmethod
    def table_name() -> str:
        return "WorkEffect"

    def __eq__(self, o: object) -> bool:
        if not isinstance(o, WorkEffect):
            return False
        if self.location_code != o.location_code:
            return False
        if self.activity_type != o.activity_type:
            return False
        if self.dimension_code != o.dimension_code:
            return False
        return True

    def __hash__(self) -> int:
        return hash((self.location_code, self.activity_type, self.dimension_code))
