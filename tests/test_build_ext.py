from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from build_ext import _cmake_configure_args, _sdk_version  # noqa: E402
from sdk_platform import SdkPlatform  # noqa: E402

SDK = Path("/sdk")
BUILD = Path("/build")


def _spec(system: str, tag: str, lib: str, wheel: str, suffix: str) -> SdkPlatform:
    return SdkPlatform(system, tag, lib, wheel, suffix)


def test_macos_args_include_deployment_target():
    args = _cmake_configure_args(
        SDK,
        BUILD,
        _spec("darwin", "macos-arm64", "libyun_sdk.a", "macosx_14_0_arm64", ".so"),
        "/py",
        "/pybind11",
    )

    assert "-DCMAKE_OSX_ARCHITECTURES=arm64" in args
    assert "-DCMAKE_OSX_DEPLOYMENT_TARGET=14.0" in args


def test_linux_args_static_link_libstdcxx():
    args = _cmake_configure_args(
        SDK,
        BUILD,
        _spec("linux", "linux-x86_64", "libyun_sdk.a", "manylinux_2_28_x86_64", ".so"),
        "/py",
        "/pybind11",
    )

    assert "-DCMAKE_MODULE_LINKER_FLAGS=-static-libstdc++ -static-libgcc" in args


def test_windows_args_use_ninja_and_clang_cl():
    args = _cmake_configure_args(
        SDK,
        BUILD,
        _spec("windows", "windows-x86_64", "yun_sdk.lib", "win_amd64", ".pyd"),
        "py.exe",
        "/pybind11",
    )

    assert "-G" in args and "Ninja" in args
    assert "-DCMAKE_CXX_COMPILER=clang-cl" in args
    assert "-DCMAKE_MSVC_RUNTIME_LIBRARY=MultiThreadedDLL" in args


def test_sdk_version_accepts_matching_pin(tmp_path: Path):
    (tmp_path / "VERSION").write_text("0.3.1\n", encoding="utf-8")

    assert _sdk_version(tmp_path, "0.3.1") == "0.3.1"


def test_sdk_version_rejects_mismatched_pin(tmp_path: Path):
    (tmp_path / "VERSION").write_text("0.3.0\n", encoding="utf-8")

    with pytest.raises(SystemExit, match="0.3.1"):
        _sdk_version(tmp_path, "0.3.1")
