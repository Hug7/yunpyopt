"""调用 C++ 求解器 ``yun`` 的入口。

本模块依赖编译产物 ``yunpyopt._core``：安装官方 wheel 即自带；源码树中由
``scripts/build_ext.py``（PEP 517 build hook）或 yun 仓库的
``scripts/build_python_extension.py`` 生成。
"""

import os
from typing import Any

try:
    from ._core import RESULT_KEYS as _CORE_RESULT_KEYS
    from ._core import Solver
except ImportError as exc:  # pragma: no cover - 仅源码树未构建时触发
    raise ImportError(
        "无法导入 yunpyopt._core。\n"
        "请确认：1) 已安装官方 wheel；2) 系统为 macOS 14.0+ arm64；"
        "3) 源码树已执行 `python scripts/build_ext.py`。"
    ) from exc

DEFAULT_LOG_LEVEL = "info"

# solve() 返回值的全部 key，顺序稳定；以 C++ 侧为准，避免两边漂移。
RESULT_KEYS = tuple(_CORE_RESULT_KEYS)

__all__ = ["Solver", "YunSolverError", "DEFAULT_LOG_LEVEL", "RESULT_KEYS", "solve"]


class YunSolverError(RuntimeError):
    """求解失败。

    原始 C++ 异常消息被原样保留在异常信息里，原始异常本身挂在 ``__cause__`` 上。
    """


def solve(
    case_dir: str | os.PathLike[str],
    log_dir: str | os.PathLike[str] | None = None,
    log_level: str = DEFAULT_LOG_LEVEL,
) -> dict[str, str | None]:
    """求解一个案例目录，返回产物文件路径。

    Args:
        case_dir: 案例目录，需包含场景 CSV 与人工编写的 ``Strategy.lua``，
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
    case_dir = os.path.abspath(os.fspath(case_dir))
    log_dir_str = os.fspath(log_dir) if log_dir is not None else ""

    try:
        solver = Solver(case_dir, log_dir_str, log_level)
    except Exception as exc:
        raise YunSolverError(f"构造 Solver 失败 (case_dir={case_dir}): {exc}") from exc

    try:
        result: dict[str, Any] = solver.solve()
    except Exception as exc:
        raise YunSolverError(f"求解失败 (case_dir={case_dir}): {exc}") from exc

    missing = [key for key in RESULT_KEYS if key not in result]
    unknown = sorted(set(result) - set(RESULT_KEYS))
    if missing or unknown:
        raise YunSolverError(
            f"求解结果 key 不匹配: missing={missing}, unknown={unknown}; "
            "通常是 yunpyopt 与 yunpyopt._core 版本不一致，请重装 wheel。"
        )

    return {key: result[key] for key in RESULT_KEYS}
