"""验证 yunpy.solver 的行为。

依赖编译产物 yunpy._core（由 yun 仓库的 BUILD_PY.sh 生成），
该产物不入库，缺失时全部用例跳过。
"""

import importlib.util
import shutil
from pathlib import Path

import pytest

from yunpy.solver import RESULT_KEYS, YunSolverError, solve

_HAS_CORE = importlib.util.find_spec("yunpy._core") is not None
pytestmark = pytest.mark.skipif(not _HAS_CORE, reason="未编译 yunpy._core，跳过")

_CASE_DIR = Path(__file__).resolve().parents[1] / "test_case" / "case1"


@pytest.fixture
def case_dir(tmp_path: Path) -> Path:
    case_path = tmp_path / "case1"
    shutil.copytree(_CASE_DIR, case_path, ignore=shutil.ignore_patterns("output"))
    return case_path


def test_solve_produces_loads(case_dir: Path) -> None:
    """正例：四个 key 齐全，loads 指向存在且非空的文件。"""
    result = solve(str(case_dir))

    assert set(result) == set(RESULT_KEYS)
    assert result["loads"] is not None, f"未产出车次，infeasible={result['infeasible']}"

    loads_path = Path(result["loads"])
    assert loads_path.is_file()
    assert loads_path.stat().st_size > 0
    assert loads_path.parent.parent == case_dir / "output"


def test_solve_repeated_is_safe(case_dir: Path) -> None:
    """同一个 case 连续求解两次不崩（覆盖 Solver::solve 的重复调用路径）。"""
    first = solve(str(case_dir))
    second = solve(str(case_dir))

    assert first["loads"] is not None and second["loads"] is not None
    assert first["loads"] != second["loads"], "两次求解应使用不同的 request_id"


def test_missing_strategy_lua_raises(tmp_path: Path) -> None:
    """负例：缺少 Strategy.lua 时抛 YunSolverError，并保留 C++ 原始消息。"""
    case_dir = tmp_path / "case_missing_lua"
    shutil.copytree(_CASE_DIR, case_dir, ignore=shutil.ignore_patterns("output", "Strategy.lua"))

    with pytest.raises(YunSolverError) as exc_info:
        solve(str(case_dir))

    assert "策略文件不存在" in str(exc_info.value)
