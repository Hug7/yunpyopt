"""Tests for yunpyopt.domain.schema.route."""

from __future__ import annotations

from yunpyopt.domain.schema.network import DistMatrix


class TestDistMatrix:
    def test_construct(self) -> None:
        dm = DistMatrix(
            from_location_code="WH001",
            to_location_code="WH002",
            dist_matrix_code=1,
            distance=5000,
            time=600,
        )
        assert dm.distance == 5000
        assert dm.time == 600
