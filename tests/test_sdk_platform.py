from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from sdk_platform import UnsupportedPlatformError, detect_platform  # noqa: E402


@pytest.mark.parametrize(
    ("system", "machine", "libc", "expected"),
    [
        (
            "darwin",
            "arm64",
            ("", ""),
            ("darwin", "macos-arm64", "libyun_sdk.a", "macosx_14_0_arm64", ".so"),
        ),
        (
            "linux",
            "x86_64",
            ("glibc", "2.28"),
            ("linux", "linux-x86_64", "libyun_sdk.a", "manylinux_2_28_x86_64", ".so"),
        ),
        (
            "linux",
            "aarch64",
            ("glibc", "2.28"),
            ("linux", "linux-arm64", "libyun_sdk.a", "manylinux_2_28_aarch64", ".so"),
        ),
        (
            "win32",
            "AMD64",
            ("", ""),
            ("windows", "windows-x86_64", "yun_sdk.lib", "win_amd64", ".pyd"),
        ),
    ],
)
def test_detect_platform_supported(system: str, machine: str, libc: tuple[str, str], expected: tuple[str, ...]):
    spec = detect_platform(system=system, machine=machine, libc=libc)

    assert (
        spec.system,
        spec.tag,
        spec.lib_name,
        spec.wheel_platform,
        spec.extension_suffix,
    ) == expected


@pytest.mark.parametrize(
    ("system", "machine", "libc"),
    [
        ("darwin", "x86_64", ("", "")),
        ("win32", "ARM64", ("", "")),
        ("linux", "x86_64", ("musl", "1.2")),
        ("freebsd", "amd64", ("", "")),
    ],
)
def test_detect_platform_unsupported(system: str, machine: str, libc: tuple[str, str]):
    with pytest.raises(UnsupportedPlatformError):
        detect_platform(system=system, machine=machine, libc=libc)
