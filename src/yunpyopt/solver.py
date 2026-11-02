"""调用 C++ 求解器 ``yun`` 的入口。

本模块依赖编译产物 ``yunpyopt._core``：安装对应平台的官方 wheel 即自带；源码树中由
``scripts/build_ext.py``（PEP 517 build hook）生成。
"""

from __future__ import annotations

import os
import sys
from typing import Any, TypedDict, cast

try:
    from ._core import RESULT_KEYS as _CORE_RESULT_KEYS
    from ._core import Solver as _CoreSolver
except ImportError as exc:  # pragma: no cover - 仅源码树未构建时触发
    raise ImportError(
        "无法导入 yunpyopt._core。\n"
        "请确认：1) 已安装对应平台的官方 wheel；2) 当前平台在支持矩阵内；"
        "3) 源码树已执行 `python scripts/build_ext.py`。"
    ) from exc

try:
    from ._build_info import SDK_PLATFORM, SDK_VERSION
except ImportError:  # pragma: no cover - 仅未构建的源码树
    SDK_PLATFORM = "unknown"
    SDK_VERSION = "unknown"

DEFAULT_LOG_LEVEL = "info"

# solve() 返回值的全部 key，顺序稳定；以 C++ 侧为准，避免两边漂移。
RESULT_KEYS = tuple(_CORE_RESULT_KEYS)

__all__ = [
    "Solver",
    "SolveResult",
    "YunSolverError",
    "DEFAULT_LOG_LEVEL",
    "RESULT_KEYS",
    "SDK_VERSION",
    "SDK_PLATFORM",
    "solve",
]


class SolveResult(TypedDict):
    """``solve()`` / ``Solver.solve()`` 的返回值。"""

    plan_summary: str | None
    loads: str | None
    locations: str | None
    unassigned: str | None
    infeasible: str | None


class YunSolverError(RuntimeError):
    """求解失败。

    原始 C++ 异常消息被原样保留在异常信息里，原始异常本身挂在 ``__cause__`` 上。
    """


class Solver:
    """对 ``_core.Solver`` 的 Python 包装。

    负责路径归一化、异常归一化与结果 key 校验；同一个实例可重复调用 ``solve()``。
    """

    def __init__(
        self,
        case_dir: str | os.PathLike[str],
        log_dir: str | os.PathLike[str] | None = None,
        log_level: str = DEFAULT_LOG_LEVEL,
    ) -> None:
        self._case_dir = os.path.abspath(os.fspath(case_dir))
        if sys.platform == "win32" and not self._case_dir.isascii():
            raise ValueError(
                "Windows 版当前仅支持 ASCII 案例路径；请把案例目录移动到纯英文路径。"
                "底层 yun SDK 仍使用窄路径，宽路径支持需要升级到 yun SDK >= 0.2.1。"
            )
        self._log_dir = os.fspath(log_dir) if log_dir is not None else ""
        self._log_level = log_level
        self._core: _CoreSolver | None = None
        try:
            self._core = _CoreSolver(self._case_dir, self._log_dir, log_level)
        except Exception as exc:
            raise YunSolverError(f"构造 Solver 失败 (case_dir={self._case_dir}): {exc}") from exc

    @property
    def output_dir(self) -> str:
        """本次请求的输出目录 ``<case_dir>/output/<request_id>``。"""
        if self._core is None:
            raise YunSolverError("Solver 已关闭")
        return cast(str, self._core.output_dir)

    @property
    def case_dir(self) -> str:
        """归一化后的案例目录绝对路径。"""
        return self._case_dir

    @property
    def log_level(self) -> str:
        return self._log_level

    def solve(self) -> SolveResult:
        """执行一次求解，返回产物路径。

        同一个实例重复调用会复用同一个 ``request_id`` 和输出目录，后一次会覆盖
        前一次的产物；需要不同 request_id 时请新建 ``Solver`` 或调用模块级
        :func:`solve`。
        """
        if self._core is None:
            raise YunSolverError("Solver 已关闭")

        try:
            raw: dict[str, Any] = self._core.solve()
        except Exception as exc:
            raise YunSolverError(f"求解失败 (case_dir={self._case_dir}): {exc}") from exc

        missing = [key for key in RESULT_KEYS if key not in raw]
        unknown = sorted(set(raw) - set(RESULT_KEYS))
        if missing or unknown:
            raise YunSolverError(
                f"求解结果 key 不匹配: missing={missing}, unknown={unknown}; "
                "通常是 yunpyopt 与 yunpyopt._core 版本不一致，请重装 wheel。"
            )
        return cast(SolveResult, {key: raw[key] for key in RESULT_KEYS})

    def close(self) -> None:
        """释放底层 solver；可重复调用。"""
        self._core = None

    def __enter__(self) -> Solver:
        return self

    def __exit__(self, *args: object) -> None:
        self.close()


def solve(
    case_dir: str | os.PathLike[str],
    log_dir: str | os.PathLike[str] | None = None,
    log_level: str = DEFAULT_LOG_LEVEL,
) -> SolveResult:
    """求解一个案例目录，返回产物文件路径。

    Args:
        case_dir: 案例目录，需包含场景 CSV 与人工编写的 ``Strategy.lua``，
            且必须可写（求解会在其下创建 ``output/<request_id>/``）。
        log_dir: 额外的日志目录。不传时该项关闭，日志仍会写到产物目录下。
        log_level: 日志等级，无法识别时 C++ 侧退化为 ``info``。

    Returns:
        key 为 ``plan_summary`` / ``loads`` / ``locations`` / ``unassigned`` /
        ``infeasible``，值为绝对路径；本次未产出的 key 为 ``None``。

        0.2.0 起新增 ``plan_summary``，指向 ``PlanSummary.json``；本次未产出时为
        ``None``。

        注意 ``loads`` 为 ``None`` 不代表失败：precheck 发现不可解订单时会拦截
        整条链路，此时 ``infeasible`` 有值而 ``loads`` 为 ``None``。

    Raises:
        ValueError: Windows 上 ``case_dir`` 含非 ASCII 字符（当前 SDK 限制）。
        YunSolverError: 场景读取失败、``Strategy.lua`` 缺失或求解过程抛异常。

    Known behaviour:
        ALNS 阶段没有把最优解写回 workspace，导出的车次是 KNN 构造解，
        因此 ``Strategy.lua`` 里的 ``max_iter`` 不影响输出。
    """
    with Solver(case_dir, log_dir=log_dir, log_level=log_level) as solver:
        return solver.solve()
