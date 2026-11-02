from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import fetch_sdk  # noqa: E402
from sdk_platform import SdkPlatform  # noqa: E402


def _spec(tag: str = "windows-x86_64") -> SdkPlatform:
    return SdkPlatform("windows", tag, "yun_sdk.lib", "win_amd64", ".pyd")


def test_sdk_name_uses_platform_tag():
    assert fetch_sdk.sdk_name("0.2.0", _spec()) == "yun-sdk-0.2.0-windows-x86_64.tar.gz"


def test_sdk_url_uses_v_prefixed_release():
    assert (
        fetch_sdk.sdk_url("0.2.0", _spec())
        == "https://github.com/Hug7/yun/releases/download/v0.2.0/yun-sdk-0.2.0-windows-x86_64.tar.gz"
    )


def test_ensure_sdk_accepts_local_dir_with_platform_lib(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    sdk = tmp_path / "sdk"
    (sdk / "lib").mkdir(parents=True)
    (sdk / "lib" / "yun_sdk.lib").write_bytes(b"x")
    monkeypatch.setenv("YUN_SDK_DIR", str(sdk))

    assert fetch_sdk.ensure_sdk("0.2.0", _spec()) == sdk.resolve()


def test_ensure_sdk_rejects_local_dir_without_platform_lib(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    sdk = tmp_path / "sdk"
    (sdk / "lib").mkdir(parents=True)
    (sdk / "lib" / "libyun_sdk.a").write_bytes(b"x")
    monkeypatch.setenv("YUN_SDK_DIR", str(sdk))

    with pytest.raises(SystemExit, match="yun_sdk.lib"):
        fetch_sdk.ensure_sdk("0.2.0", _spec())
