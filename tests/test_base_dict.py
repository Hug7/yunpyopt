"""Tests for yunpyopt.domain.schema.base_dict."""

from __future__ import annotations

from yunpyopt.domain.schema.base_dict import Dimension, Label, LabelApply, LabelValue


class TestDimension:
    def test_construct_minimal(self) -> None:
        d = Dimension(code="WEIGHT", precision=2)
        assert d.code == "WEIGHT"
        assert d.precision == 2
        assert d.name is None

    def test_construct_full(self) -> None:
        d = Dimension(code="WEIGHT", precision=2, name="Weight")
        assert d.name == "Weight"


class TestLabel:
    def test_construct_minimal(self) -> None:
        lb = Label(code="REFRIGERATED")
        assert lb.code == "REFRIGERATED"
        assert lb.name is None

    def test_construct_full(self) -> None:
        lb = Label(code="REFRIGERATED", name="Refrigerated")
        assert lb.name == "Refrigerated"


class TestLabelValue:
    def test_construct(self) -> None:
        lv = LabelValue(label_code="REFRIGERATED", label_value="YES")
        assert lv.label_code == "REFRIGERATED"
        assert lv.label_value == "YES"


class TestLabelApply:
    def test_construct(self) -> None:
        la = LabelApply(label_code="REFRIGERATED", apply_item="VehicleModel")
        assert la.label_code == "REFRIGERATED"
        assert la.apply_item == "VehicleModel"
