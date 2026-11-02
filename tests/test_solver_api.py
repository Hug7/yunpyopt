from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from yunpyopt import SDK_PLATFORM, SDK_VERSION, Solver

_CASE_DIR = Path(__file__).resolve().parent / "data" / "c1_2_1"


@pytest.fixture
def case_dir(tmp_path: Path) -> Path:
    path = tmp_path / "c1_2_1"
    shutil.copytree(_CASE_DIR, path, ignore=shutil.ignore_patterns("output"))
    return path


def test_build_info_is_available():
    assert SDK_VERSION == "0.2.0"
    assert SDK_PLATFORM in {
        "macos-arm64",
        "linux-x86_64",
        "linux-arm64",
        "windows-x86_64",
    }


def test_solver_context_manager_and_reuse(case_dir: Path):
    with Solver(case_dir, log_level="warning") as solver:
        first = solver.solve()
        second = solver.solve()
        assert Path(solver.output_dir).is_dir()

    assert first["loads"] is not None
    assert second["loads"] is not None
    # 同一个 Solver 复用同一个 request_id/输出目录，重复求解会覆盖同一批产物。
    assert first["loads"] == second["loads"]
    assert Path(first["loads"]).is_file()


def test_solver_result_has_plan_summary(case_dir: Path):
    with Solver(case_dir, log_level="warning") as solver:
        result = solver.solve()

    assert result["plan_summary"] is not None
    assert json.loads(Path(result["plan_summary"]).read_text(encoding="utf-8"))
