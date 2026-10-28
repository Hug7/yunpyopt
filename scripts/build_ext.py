"""PEP 517 build hook: 用 yun 预编译 SDK 构建 pybind11 扩展。

不再需要 yun 源码或 conan；SDK 由 yun 的 GitHub Release 提供。
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

from fetch_sdk import ensure_sdk

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "src" / "yunpyopt"
BUILD_DIR = ROOT / "build" / "yun-sdk-binding"
TARGET = "yun_python_binding"


def _run(cmd: list[str]) -> None:
    print("+", " ".join(str(part) for part in cmd), flush=True)
    subprocess.run(cmd, check=True)


def _pybind11_cmakedir() -> str:
    try:
        return subprocess.check_output(
            [sys.executable, "-m", "pybind11", "--cmakedir"],
            text=True,
        ).strip()
    except (subprocess.CalledProcessError, FileNotFoundError) as exc:
        raise SystemExit("需要 pybind11；它应由 PEP 517 build-system requires 安装。") from exc


def build() -> None:
    if shutil.which("cmake") is None:
        raise SystemExit("需要 cmake：brew install cmake")

    sdk = ensure_sdk()
    if BUILD_DIR.exists():
        shutil.rmtree(BUILD_DIR)

    _run(
        [
            "cmake",
            "-S",
            str(sdk),
            "-B",
            str(BUILD_DIR),
            "-DCMAKE_BUILD_TYPE=Release",
            f"-DPython3_EXECUTABLE={sys.executable}",
            f"-Dpybind11_DIR={_pybind11_cmakedir()}",
            f"-DCMAKE_OSX_DEPLOYMENT_TARGET={os.environ.get('MACOSX_DEPLOYMENT_TARGET', '14.0')}",
            "-DCMAKE_SKIP_RPATH=ON",
            "-DCMAKE_OSX_ARCHITECTURES=arm64",
        ]
    )
    _run(
        [
            "cmake",
            "--build",
            str(BUILD_DIR),
            "--target",
            TARGET,
            "-j",
            str(os.cpu_count() or 1),
        ]
    )

    modules = sorted(BUILD_DIR.glob("_core*.so"))
    if len(modules) != 1:
        raise SystemExit(f"构建目录中应恰好有一个 _core*.so，实际: {modules}")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for stale in OUT_DIR.glob("_core.*.so"):
        stale.unlink()
    target = OUT_DIR / modules[0].name
    shutil.copy2(modules[0], target)
    print(f"已复制扩展: {target}", flush=True)

    code = (
        "import importlib.util;"
        f"path = {str(target)!r};"
        "spec = importlib.util.spec_from_file_location('_core', path);"
        "mod = importlib.util.module_from_spec(spec);"
        "spec.loader.exec_module(mod);"
        "print('RESULT_KEYS', mod.RESULT_KEYS)"
    )
    _run([sys.executable, "-c", code])


if __name__ == "__main__":
    build()
