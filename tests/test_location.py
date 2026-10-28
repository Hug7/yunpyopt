"""Tests for yunpyopt.domain.schema.location."""

from __future__ import annotations

from yunpyopt.domain.schema.location import (
    Location,
    LocationAvailableVehicle,
    LocationLabelValue,
    WorkCalendarDaily,
    WorkCalendarWeekly,
    WorkEffect,
    WorkFixed,
)


class TestLocation:
    def test_construct_minimal(self) -> None:
        loc = Location(code="WH001", lng=121.5, lat=31.2)
        assert loc.code == "WH001"
        assert loc.name is None

    def test_construct_full(self) -> None:
        loc = Location(code="WH001", lng=121.5, lat=31.2, name="Shanghai")
        assert loc.name == "Shanghai"


class TestLocationLabelValue:
    def test_construct(self) -> None:
        llv = LocationLabelValue(location_code="WH001", label_code="ZONE", label_value="DOWNTOWN")
        assert llv.location_code == "WH001"


class TestLocationAvailableVehicle:
    def test_construct(self) -> None:
        lav = LocationAvailableVehicle(location_code="WH001", carrier_code="C1", vehicle_model_code="VM1")
        assert lav.carrier_code == "C1"


class TestWorkCalendarDaily:
    def test_construct(self) -> None:
        wcd = WorkCalendarDaily(location_code="WH001", calendar_type="PICK", daily="09001700")
        assert wcd.calendar_type == "PICK"


class TestWorkCalendarWeekly:
    def test_construct(self) -> None:
        wcw = WorkCalendarWeekly(
            location_code="WH001",
            calendar_type="PICK",
            monday="09001700",
            tuesday="09001700",
        )
        assert wcw.monday == "09001700"
        assert wcw.sunday is None


class TestWorkFixed:
    def test_construct(self) -> None:
        wf = WorkFixed(location_code="WH001", fixed_pick_time=600)
        assert wf.fixed_pick_time == 600
        assert wf.fixed_drop_time is None


class TestWorkEffect:
    def test_construct(self) -> None:
        we = WorkEffect(
            location_code="WH001",
            activity_type="PICK",
            dimension_code="WEIGHT",
            per_hour_process_quantity=100.0,
        )
        assert we.per_hour_process_quantity == 100.0
