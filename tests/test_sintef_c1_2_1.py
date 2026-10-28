"""SINTEF Homberger C1_2_1 夹具的结构与求解冒烟测试。

夹具由 ``scripts/convert_sintef_vrptw.py`` 生成，表结构与 ``tests/data/c1_2_1``
一致。这里校验转换后的关键不变量，并在扩展可用时真实求解一次。
"""

from __future__ import annotations

import csv
import json
import shutil
from datetime import datetime
from pathlib import Path

import pytest

_CASE_DIR = Path(__file__).resolve().parent / "data" / "c1_2_1"
_BASE_DATETIME = datetime(2026, 1, 1)
_HORIZON_MINUTES = 1351
_CUSTOMER_CODES = {f"C{index:03d}" for index in range(1, 201)}


def _rows(table: str) -> list[dict[str, str]]:
    with (_CASE_DIR / table).open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _minutes(value: str) -> float:
    return (datetime.strptime(value, "%Y-%m-%d %H:%M") - _BASE_DATETIME).total_seconds() / 60


def test_case_covers_all_sintef_customers() -> None:
    locations = _rows("Location.csv")
    orders = _rows("CargoOrder.csv")

    assert len(locations) == 201
    assert {row["Code"] for row in locations} == {"DEPOT"} | _CUSTOMER_CODES
    assert len(orders) == 200
    assert {row["PickLocationCode"] for row in orders} == {"DEPOT"}
    assert {row["DropLocationCode"] for row in orders} == _CUSTOMER_CODES
    assert len(_rows("CargoSubOrder.csv")) == 200
    assert len(_rows("CargoSubOrderDimensionValue.csv")) == 200


def test_time_windows_follow_the_instance_horizon() -> None:
    for order in _rows("CargoOrder.csv"):
        earliest_pick = _minutes(order["EarliestPickDateTime"])
        latest_pick = _minutes(order["LatestPickDateTime"])
        earliest_drop = _minutes(order["EarliestDropDateTime"])
        latest_drop = _minutes(order["LatestDropDateTime"])

        assert 0 <= earliest_pick <= latest_pick <= _HORIZON_MINUTES
        assert 0 <= earliest_drop <= latest_drop <= _HORIZON_MINUTES
        assert earliest_pick <= earliest_drop

    work_fixed = {row["LocationCode"]: row for row in _rows("WorkFixed.csv")}
    assert int(work_fixed["DEPOT"]["FixedDropTime"]) == 0
    assert all(int(work_fixed[code]["FixedDropTime"]) == 90 * 60 for code in _CUSTOMER_CODES)


def test_distance_matrix_is_complete_and_symmetric() -> None:
    rows = _rows("DistMatrix.csv")
    assert len(rows) == 201 * 200

    distances = {(row["FromLocationCode"], row["ToLocationCode"]): int(row["Distance"]) for row in rows}
    assert len(distances) == 201 * 200
    assert all(distances[(target, source)] == distance for (source, target), distance in distances.items())

    for row in rows:
        distance = int(row["Distance"])
        time = int(row["Time"])
        assert abs(time - distance * 60 / 1000) <= 1


def test_capacity_matches_the_sintef_instance() -> None:
    demand = sum(float(row["DimensionValue"]) for row in _rows("CargoSubOrderDimensionValue.csv"))
    assert demand == 3530

    vehicle_models = _rows("VehicleModelDimensionValue.csv")
    assert [(row["DimensionCode"], float(row["DimensionValue"])) for row in vehicle_models] == [("weight", 200)]

    vehicles = _rows("Vehicle.csv")
    assert len(vehicles) == 1
    assert vehicles[0]["OriginLocationCode"] == "DEPOT"
    assert vehicles[0]["DestinationLocationCode"] == "DEPOT"
    # 原始实例是 50 辆；夹具留出余量，避免 KNN 车辆耗尽时丢单。
    assert int(vehicles[0]["Count"]) == 60


def test_solve_assigns_every_customer(tmp_path: Path) -> None:
    pytest.importorskip("yunpyopt._core")
    from yunpyopt import solve

    case_dir = tmp_path / "c1_2_1"
    shutil.copytree(_CASE_DIR, case_dir, ignore=shutil.ignore_patterns("output"))

    result = solve(case_dir, log_level="warning")
    assert result["loads"] is not None, f"未产出车次，infeasible={result['infeasible']}"

    loads = json.loads(Path(result["loads"]).read_text(encoding="utf-8"))
    visits = [location for load in loads for location in load["LocationSequences"] if location.startswith("C")]
    assert len(loads) <= 60
    assert len(visits) == 200
    assert set(visits) == _CUSTOMER_CODES

    unassigned = json.loads(Path(result["unassigned"]).read_text(encoding="utf-8"))
    assert unassigned == []

    carried_weight = sum(
        dimension["DimensionValue"]
        for load in loads
        for dimension in load["LoadDimensions"]
        if dimension["DimensionCode"] == "weight"
    )
    assert carried_weight == 3530
