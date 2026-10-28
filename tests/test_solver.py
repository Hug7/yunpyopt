"""验证 yunpyopt.solver 的行为。

依赖编译产物 yunpyopt._core（由 scripts/build_ext.py 生成）。
缺失时默认整模块跳过；CI 设置 YUNPYOPT_REQUIRE_CORE=1 时缺失即失败，
避免“全 skip 也算绿”。
"""

import importlib.util
import os
import shutil
from pathlib import Path

import pytest

_HAS_CORE = importlib.util.find_spec("yunpyopt._core") is not None

if not _HAS_CORE:
    if os.environ.get("YUNPYOPT_REQUIRE_CORE") == "1":
        raise RuntimeError("YUNPYOPT_REQUIRE_CORE=1 但 yunpyopt._core 不存在；请先构建扩展")
    pytest.skip("未构建 yunpyopt._core，跳过", allow_module_level=True)

from yunpyopt.solver import RESULT_KEYS, YunSolverError, solve  # noqa: E402

_CASE_DIR = Path(__file__).resolve().parent / "data" / "c1_2_1"


@pytest.fixture
def case_dir(tmp_path: Path) -> Path:
    case_path = tmp_path / "c1_2_1"
    shutil.copytree(_CASE_DIR, case_path, ignore=shutil.ignore_patterns("output"))
    return case_path


def test_solve_produces_loads(case_dir: Path) -> None:
    """正例：四个 key 齐全，loads 指向存在且非空的文件。"""
    result = solve(case_dir)  # 同时覆盖 PathLike 入参

    assert set(result) == set(RESULT_KEYS)
    assert result["loads"] is not None, f"未产出车次，infeasible={result['infeasible']}"

    loads_path = Path(result["loads"])
    assert loads_path.is_file()
    assert loads_path.stat().st_size > 0
    assert loads_path.parent.parent == case_dir / "output"


def test_solve_repeated_is_safe(case_dir: Path) -> None:
    """同一个 case 连续求解两次不崩（覆盖 Solver::solve 的重复调用路径）。"""
    first = solve(case_dir)
    second = solve(case_dir)

    assert first["loads"] is not None and second["loads"] is not None
    assert first["loads"] != second["loads"], "两次求解应使用不同的 request_id"


def test_missing_strategy_lua_raises(tmp_path: Path) -> None:
    """负例：缺少 Strategy.lua 时抛 YunSolverError，并保留 C++ 原始消息。"""
    case_dir = tmp_path / "case_missing_lua"
    shutil.copytree(_CASE_DIR, case_dir, ignore=shutil.ignore_patterns("output", "Strategy.lua"))

    with pytest.raises(YunSolverError) as exc_info:
        solve(case_dir)

    assert "策略文件不存在" in str(exc_info.value)


def test_result_keys_match_binding() -> None:
    """Python 侧 RESULT_KEYS 必须与 C++ 绑定暴露的一致。"""
    from yunpyopt._core import RESULT_KEYS as CORE_RESULT_KEYS

    assert tuple(CORE_RESULT_KEYS) == RESULT_KEYS
