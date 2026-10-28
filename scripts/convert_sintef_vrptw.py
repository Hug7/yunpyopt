"""把 SINTEF/Solomon VRPTW 文本实例转换为 yun 案例目录。

输入是 SINTEF TOP 页面（https://www.sintef.no/projectweb/top/vrptw/）上的
``*.TXT`` 实例，格式为::

    <name>

    VEHICLE
    NUMBER     CAPACITY
      50          200

    CUSTOMER
    CUST NO.  XCOORD.    YCOORD.    DEMAND   READY TIME  DUE DATE   SERVICE TIME
    0         70         70         0        0           1351       0
    1         33         78         20       750         809        90
    ...

输出是与 ``tests/data/c1_2_1`` 相同的表结构（CSV + ``Parameter.yaml`` +
``Strategy.lua``），供 ``yunpyopt.solve`` 直接求解。

转换约定（Homberger/Solomon 的时间与距离单位都是“分钟”）：

* 1 个距离单位 = 1 分钟行驶时间 = 1000 米；
* 1 个时间单位 = 1 分钟，所有时刻平移到 ``BASE_DATETIME``
  （``CargoOrder`` 的最小精度是分钟，不能直接写相对时间）；
* 客户服务时间写入 ``WorkFixed.FixedDropTime``（秒）；
* 需求量写入 ``weight`` 维度，车辆容量写入同一维度；
* 每个客户一条 ``CargoOrder``：从车场提货、送到客户；
* 车场车辆的起点/终点都是车场，保证车次回场；
* yun 以“最晚客户 due”作为计划结束时间。若车场 due 更晚，会把最晚 due
  的客户窗口放宽到车场 due，以保留“车辆在车场关闭前回场”的语义；
* 当前 KNN 构造在车辆耗尽时可能丢单，``--vehicles`` 可覆盖车辆数留出余量。

用法::

    python scripts/convert_sintef_vrptw.py C1_2_1.TXT tests/data/c1_2_1 --vehicles 60
"""

from __future__ import annotations

import argparse
import csv
import math
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path

BASE_DATETIME = datetime(2026, 1, 1, 0, 0)
SECONDS_PER_MINUTE = 60
METERS_PER_DISTANCE_UNIT = 1000

DEPOT_CODE = "DEPOT"
CARRIER_CODE = "SINTEF"
VEHICLE_MODEL_CODE = "TRUCK"
DIST_MATRIX_CODE = "EUCLID"
WEIGHT_DIMENSION = "weight"

STRATEGY_LUA = """\
-- 由 scripts/convert_sintef_vrptw.py 生成。
-- 只做 KNN 构造并快照：测试用例不依赖 ALNS 的随机迭代，求解快且可复现。
function solve()
    construct_knn()
    snapshot("A")
end
"""


@dataclass(frozen=True)
class Customer:
    """实例中的一行客户（0 号为车场）。"""

    index: int
    x: int
    y: int
    demand: int
    ready: int
    due: int
    service: int

    @property
    def code(self) -> str:
        return DEPOT_CODE if self.index == 0 else f"C{self.index:03d}"

    @property
    def name(self) -> str:
        return "Depot" if self.index == 0 else f"Customer {self.index:03d}"


@dataclass(frozen=True)
class Instance:
    name: str
    vehicle_count: int
    capacity: int
    customers: list[Customer]

    @property
    def depot(self) -> Customer:
        return self.customers[0]


def parse_instance(path: Path) -> Instance:
    """解析 SINTEF/Solomon 文本实例。"""
    lines = [line.strip() for line in path.read_text(encoding="utf-8").splitlines()]
    if not lines or not lines[0]:
        raise ValueError(f"{path} 为空或缺少实例名")

    name = lines[0]
    vehicle_header = _index_of(lines, "VEHICLE")
    customer_header = _index_of(lines, "CUSTOMER")

    vehicle_numbers = _first_int_row(lines[vehicle_header + 1 : customer_header], expected=2)
    vehicle_count, capacity = vehicle_numbers

    customers = [Customer(*values) for values in _int_rows(lines[customer_header + 1 :], expected=7)]
    if not customers:
        raise ValueError(f"{path} 中没有客户数据")
    if customers[0].index != 0:
        raise ValueError("第一行客户必须是 0 号车场")
    if [customer.index for customer in customers] != list(range(len(customers))):
        raise ValueError("客户编号必须从 0 开始连续递增")

    return Instance(name=name, vehicle_count=vehicle_count, capacity=capacity, customers=customers)


def _index_of(lines: Sequence[str], marker: str) -> int:
    for index, line in enumerate(lines):
        if line == marker:
            return index
    raise ValueError(f"实例中缺少 {marker} 段")


def _ints(line: str) -> list[int]:
    parts = line.split()
    if not parts or not all(_is_int(part) for part in parts):
        return []
    return [int(part) for part in parts]


def _is_int(text: str) -> bool:
    return text.lstrip("-").isdigit()


def _first_int_row(lines: Iterable[str], expected: int) -> list[int]:
    for line in lines:
        values = _ints(line)
        if len(values) == expected:
            return values
    raise ValueError(f"没有找到 {expected} 个整数的数据行")


def _int_rows(lines: Iterable[str], expected: int) -> list[list[int]]:
    for line in lines:
        values = _ints(line)
        if len(values) == expected:
            yield values


def _time(minutes: int) -> str:
    return (BASE_DATETIME + timedelta(minutes=minutes)).strftime("%Y-%m-%d %H:%M")


def _write_csv(path: Path, header: Sequence[str], rows: Iterable[Sequence[object]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(header)
        writer.writerows(rows)


def _write_static_tables(root: Path, instance: Instance, latest_due: dict[int, int]) -> None:
    # Dimension / Label（本用例不使用标签，保留空表）
    _write_csv(root / "Dimension.csv", ["Code", "Precision", "Name"], [[WEIGHT_DIMENSION, 2, WEIGHT_DIMENSION]])
    _write_csv(root / "Label.csv", ["Code", "Name"], [])
    _write_csv(root / "LabelValue.csv", ["LabelCode", "LabelValue"], [])
    _write_csv(root / "LabelApply.csv", ["LabelCode", "ApplyItem"], [])

    # 站点：Homberger 的平面坐标直接写入 Lng/Lat 字段（路由只使用 DistMatrix）
    _write_csv(
        root / "Location.csv",
        ["Code", "Name", "Lng", "Lat"],
        [[customer.code, customer.name, customer.x, customer.y] for customer in instance.customers],
    )
    _write_csv(root / "LocationLabelValue.csv", ["LocationCode", "LabelCode", "LabelValue"], [])
    _write_csv(
        root / "LocationAvailableVehicle.csv",
        ["LocationCode", "CarrierCode", "VehicleModelCode"],
        [[customer.code, CARRIER_CODE, VEHICLE_MODEL_CODE] for customer in instance.customers],
    )

    # 工作日历留空；时间窗由 CargoOrder 表达
    _write_csv(root / "WorkCalendarDaily.csv", ["LocationCode", "CalendarType", "Daily"], [])
    _write_csv(
        root / "WorkCalendarWeekly.csv",
        ["LocationCode", "CalendarType", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"],
        [],
    )
    _write_csv(
        root / "WorkEffect.csv",
        ["LocationCode", "ActivityType", "DimensionCode", "PerHourProcessQuantity"],
        [],
    )
    _write_csv(
        root / "WorkFixed.csv",
        ["LocationCode", "FixedPickTime", "FixedDropTime"],
        [
            [
                customer.code,
                0,
                customer.service * SECONDS_PER_MINUTE if customer.index != 0 else 0,
            ]
            for customer in instance.customers
        ],
    )

    # 车型 / 承运商 / 车辆
    _write_csv(root / "DistMatrixCode.csv", ["Code", "Name"], [[DIST_MATRIX_CODE, DIST_MATRIX_CODE]])
    _write_csv(
        root / "VehicleModel.csv",
        ["Code", "Name", "DistMatrixCode"],
        [[VEHICLE_MODEL_CODE, f"{instance.capacity}-unit truck", DIST_MATRIX_CODE]],
    )
    _write_csv(
        root / "VehicleModelDimensionValue.csv",
        ["VehicleModelCode", "DimensionCode", "DimensionValue"],
        [[VEHICLE_MODEL_CODE, WEIGHT_DIMENSION, instance.capacity]],
    )
    _write_csv(root / "VehicleModelLabelValue.csv", ["VehicleModelCode", "LabelCode", "LabelValue"], [])
    _write_csv(root / "Carrier.csv", ["Code", "Name"], [[CARRIER_CODE, CARRIER_CODE]])
    _write_csv(root / "CarrierLabelValue.csv", ["CarrierCode", "LabelCode", "LabelValue"], [])
    _write_csv(
        root / "Vehicle.csv",
        ["CarrierCode", "VehicleModelCode", "Count", "OriginLocationCode", "DestinationLocationCode"],
        [[CARRIER_CODE, VEHICLE_MODEL_CODE, instance.vehicle_count, DEPOT_CODE, DEPOT_CODE]],
    )

    # 订单：车场提货 -> 客户送达
    _write_csv(
        root / "CargoOrder.csv",
        [
            "Code",
            "Name",
            "PickLocationCode",
            "DropLocationCode",
            "EarliestPickDateTime",
            "LatestPickDateTime",
            "EarliestDropDateTime",
            "LatestDropDateTime",
        ],
        [
            [
                f"ORD{customer.index:03d}",
                "",
                DEPOT_CODE,
                customer.code,
                _time(instance.depot.ready),
                _time(instance.depot.due),
                _time(customer.ready),
                _time(latest_due[customer.index]),
            ]
            for customer in instance.customers[1:]
        ],
    )
    _write_csv(
        root / "CargoSubOrder.csv",
        ["CargoOrderCode", "CargoSubOrderCode", "CargoSubOrderName", "Quantity"],
        [[f"ORD{customer.index:03d}", f"ORD{customer.index:03d}_0", "", 1] for customer in instance.customers[1:]],
    )
    _write_csv(
        root / "CargoSubOrderDimensionValue.csv",
        ["CargoOrderCode", "CargoSubOrderCode", "DimensionCode", "DimensionValue"],
        [
            [f"ORD{customer.index:03d}", f"ORD{customer.index:03d}_0", WEIGHT_DIMENSION, customer.demand]
            for customer in instance.customers[1:]
        ],
    )
    _write_csv(
        root / "CargoSubOrderLabelValue.csv",
        ["CargoOrderCode", "CargoSubOrderCode", "LabelCode", "LabelValue"],
        [],
    )

    # 计费表留空（ChargeRule 无规则时求解器自动关闭计费）
    _write_csv(root / "ChargeCode.csv", ["Code", "Name"], [])
    _write_csv(
        root / "ChargeRule.csv",
        [
            "RuleCode",
            "ChargeCode",
            "ChargeSecondaryCode",
            "CarrierCode",
            "VehicleModelCode",
            "ChargePathType",
            "LocationLabelCode",
            "ChargePathLabelValues",
            "TierConditionType",
            "TierDimensionCode",
        ],
        [],
    )
    _write_csv(root / "ChargeTier.csv", ["RuleCode", "TierSeq", "LowerBound", "UpperBound"], [])
    _write_csv(root / "ChargeItem.csv", ["RuleCode", "TierSeq", "ItemType", "Price", "DimensionCode"], [])


def _write_dist_matrix(root: Path, instance: Instance) -> None:
    customers = instance.customers
    rows: list[list[object]] = []
    for source in customers:
        for target in customers:
            if source.index == target.index:
                continue
            distance = math.hypot(source.x - target.x, source.y - target.y)
            rows.append(
                [
                    source.code,
                    target.code,
                    DIST_MATRIX_CODE,
                    round(distance * METERS_PER_DISTANCE_UNIT),
                    round(distance * SECONDS_PER_MINUTE),
                ]
            )
    _write_csv(
        root / "DistMatrix.csv",
        ["FromLocationCode", "ToLocationCode", "DistMatrixCode", "Distance", "Time"],
        rows,
    )


def _write_config(root: Path, instance: Instance) -> None:
    (root / "Parameter.yaml").write_text(
        "\n".join(
            [
                f"start_time: {_time(instance.depot.ready)}",
                f"end_time: {_time(instance.depot.due)}",
                "strategy_file: Strategy.lua",
                "load_unload_policy: FILO",
                "",
            ]
        ),
        encoding="utf-8",
    )
    (root / "Strategy.lua").write_text(STRATEGY_LUA, encoding="utf-8")


def _extend_latest_due(instance: Instance, plan_end: int) -> dict[int, int]:
    """返回每个客户的 drop 最晚时刻。

    yun 用 ``min(Parameter.end_time, max(客户 latest drop))`` 作为计划结束时间。
    要把计划结束时间保持在车场 due，需要至少一个订单的 latest drop 达到它：
    这里只放宽“本来就最晚”的客户，其余客户窗口保持不变。
    """
    due_by_customer = {customer.index: customer.due for customer in instance.customers[1:]}
    max_due = max(due_by_customer.values())
    if plan_end <= max_due:
        return due_by_customer

    extended = 0
    for index, due in due_by_customer.items():
        if due == max_due:
            due_by_customer[index] = plan_end
            extended += 1
    print(f"注意: 将 {extended} 个 due={max_due} 的客户窗口放宽到车场 due={plan_end}")
    return due_by_customer


def convert(instance_path: Path, output_dir: Path, vehicles: int | None = None) -> Instance:
    instance = parse_instance(instance_path)
    if vehicles is not None:
        instance = Instance(
            name=instance.name,
            vehicle_count=vehicles,
            capacity=instance.capacity,
            customers=instance.customers,
        )
    output_dir.mkdir(parents=True, exist_ok=True)
    latest_due = _extend_latest_due(instance, instance.depot.due)
    _write_static_tables(output_dir, instance, latest_due)
    _write_dist_matrix(output_dir, instance)
    _write_config(output_dir, instance)
    return instance


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="把 SINTEF/Solomon VRPTW 实例转换为 yun 案例目录")
    parser.add_argument("instance", type=Path, help="实例 TXT 路径，例如 C1_2_1.TXT")
    parser.add_argument("output_dir", type=Path, help="输出案例目录")
    parser.add_argument(
        "--vehicles",
        type=int,
        default=None,
        help="覆盖实例中的车辆数；当前 KNN 构造在车辆耗尽时可能丢单，测试夹具通常留余量",
    )
    args = parser.parse_args(argv)

    instance = convert(args.instance, args.output_dir, args.vehicles)
    print(
        f"{instance.name}: {len(instance.customers) - 1} customers, "
        f"{instance.vehicle_count} vehicles, capacity {instance.capacity}"
    )
    print(f"已生成案例: {args.output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
