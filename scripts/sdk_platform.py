"""平台识别与 yun SDK 元数据。

`fetch_sdk.py`、`build_ext.py`、`fix_wheel_tag.py` 共用这一份映射，避免三处各写
一套平台判断。只覆盖 yun SDK 0.2.0 正式提供的四个平台产物。
"""

from __future__ import annotations

import platform
import sys
from dataclasses import dataclass


class UnsupportedPlatformError(RuntimeError):
    """当前平台没有对应的 yun SDK 产物。"""


@dataclass(frozen=True)
class SdkPlatform:
    """一个 SDK 平台的构建元数据。"""

    system: str  # darwin | linux | windows
    tag: str
    lib_name: str
    wheel_platform: str
    extension_suffix: str


_MACHINE_ALIASES = {
    "x86_64": "x86_64",
    "amd64": "x86_64",
    "arm64": "arm64",
    "aarch64": "arm64",
}


def _normalize_machine(machine: str) -> str:
    try:
        return _MACHINE_ALIASES[machine.lower()]
    except KeyError as exc:
        raise UnsupportedPlatformError(f"不支持的 CPU 架构: {machine}") from exc


def detect_platform(
    system: str | None = None,
    machine: str | None = None,
    libc: tuple[str, str] | None = None,
) -> SdkPlatform:
    """返回当前（或显式指定）平台的 SDK 元数据。"""
    system = system or sys.platform
    machine = _normalize_machine(machine or platform.machine())

    if system == "darwin":
        if machine != "arm64":
            raise UnsupportedPlatformError("yun SDK 不提供 macOS Intel（x86_64）产物")
        return SdkPlatform("darwin", "macos-arm64", "libyun_sdk.a", "macosx_14_0_arm64", ".so")

    if system.startswith("linux"):
        libc_name, _ = libc if libc is not None else platform.libc_ver()
        if libc_name != "glibc":
            raise UnsupportedPlatformError(
                f"yun SDK 只支持 glibc Linux（manylinux_2_28），当前 libc={libc_name or 'unknown'}"
            )
        if machine == "x86_64":
            return SdkPlatform("linux", "linux-x86_64", "libyun_sdk.a", "manylinux_2_28_x86_64", ".so")
        if machine == "arm64":
            return SdkPlatform("linux", "linux-arm64", "libyun_sdk.a", "manylinux_2_28_aarch64", ".so")
        raise UnsupportedPlatformError(f"yun SDK 不提供 Linux {machine} 产物")

    if system == "win32":
        if machine != "x86_64":
            raise UnsupportedPlatformError("yun SDK 不提供 Windows arm64 产物")
        return SdkPlatform("windows", "windows-x86_64", "yun_sdk.lib", "win_amd64", ".pyd")

    raise UnsupportedPlatformError(f"yun SDK 不支持当前平台: {system}/{machine}")
