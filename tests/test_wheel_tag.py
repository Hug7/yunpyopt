from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from fix_wheel_tag import _platform_tag, _python_abi  # noqa: E402


def test_macos_minos_rounds_up_to_next_major():
    assert _platform_tag("13.3", "arm64") == "macosx_14_0_arm64"
    assert _platform_tag("14.0", "arm64") == "macosx_14_0_arm64"


def test_python_abi_from_extension_name():
    assert _python_abi(Path("_core.cpython-311-darwin.so")) == ("cp311", "cp311")


def test_python_abi_from_linux_extension_name():
    assert _python_abi(Path("_core.cpython-311-x86_64-linux-gnu.so")) == ("cp311", "cp311")


def test_python_abi_supports_pyd():
    assert _python_abi(Path("_core.cp311-win_amd64.pyd")) == ("cp311", "cp311")
