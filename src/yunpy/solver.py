"""调用 C++ 求解器 ``yun`` 的入口。

本模块依赖编译产物 ``yunpy._core``（由 yun 仓库的 ``BUILD_PY.sh`` 生成）。
该产物不入库，缺失时 import 会失败，所以没有被 ``yunpy/__init__.py`` 引入。
"""

import os
from typing import Any

from yunpy._core import Solver  # type: ignore[import-not-found]

DEFAULT_LOG_LEVEL = "info"

# solve() 返回值的全部 key，顺序稳定
RESULT_KEYS = ("loads", "locations", "unassigned", "infeasible")

__all__ = ["Solver", "YunSolverError", "DEFAULT_LOG_LEVEL", "RESULT_KEYS", "solve"]


class YunSolverError(RuntimeError):
    """求解失败。

    原始 C++ 异常消息被原样保留在异常信息里，原始异常本身挂在 ``__cause__`` 上。
    """


def solve(
    case_dir: str,
    log_dir: str | None = None,
    log_level: str = DEFAULT_LOG_LEVEL,
) -> dict[str, str | None]:
    """求解一个案例目录，返回产物文件路径。

    Args:
        case_dir: 案例目录，需包含 22 个场景 CSV 与人工编写的 ``Strategy.lua``，
            且必须可写（求解会在其下创建 ``output/<request_id>/``）。
        log_dir: 额外的日志目录。不传时该项关闭，日志仍会写到产物目录下。
        log_level: 日志等级，无法识别时 C++ 侧退化为 ``info``。

    Returns:
        key 为 ``loads`` / ``locations`` / ``unassigned`` / ``infeasible``，
        值为绝对路径；本次未产出的 key 为 ``None``。

        注意 ``loads`` 为 ``None`` 不代表失败：precheck 发现不可解订单时会拦截
        整条链路，此时 ``infeasible`` 有值而 ``loads`` 为 ``None``。

    Raises:
        YunSolverError: 场景读取失败、``Strategy.lua`` 缺失或求解过程抛异常。

    Known behaviour:
        ALNS 阶段没有把最优解写回 workspace，导出的车次是 KNN 构造解，
        因此 ``Strategy.lua`` 里的 ``max_iter`` 不影响输出。
    """
    case_dir = os.path.abspath(case_dir)
    try:
        solver = Solver(case_dir, log_dir or "", log_level)
    except Exception as exc:
        raise YunSolverError(f"构造 Solver 失败 (case_dir={case_dir}): {exc}") from exc

    try:
        result: dict[str, Any] = solver.solve()
    except Exception as exc:
        raise YunSolverError(f"求解失败 (case_dir={case_dir}): {exc}") from exc

    return {key: result[key] for key in RESULT_KEYS}
