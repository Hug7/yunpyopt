#!/usr/bin/env python3
"""按平台修正/校验 wheel 标签。

- macOS：poetry-core 用构建解释器的 ``sys_tags``（例如 ``macosx_11_0_arm64``）作为
  标签，但扩展的实际 minos 更高。脚本读取 ``LC_BUILD_VERSION/minos`` 与 ``lipo``
  架构，把 minos 向上取整到下一个 major（13.3 -> 14_0），再调用 ``wheel tags``
  重写文件名、``WHEEL`` 与 ``RECORD``。
- Linux：调用 ``auditwheel repair --only-plat`` 把 wheel 修成单一 manylinux_2_28 标签，并校验结果。
- Windows：校验 ``win_amd64`` 标签与唯一的 ``yunpyopt/_core*.pyd``。
"""

from __future__ import annotations

import argparse
import importlib.util
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

from sdk_platform import SdkPlatform, detect_platform


def _run(cmd: list[str]) -> str:
    print("+", " ".join(cmd), flush=True)
    result = subprocess.run(cmd, check=True, text=True, capture_output=True)
    if result.stdout:
        print(result.stdout, end="", flush=True)
    if result.stderr:
        print(result.stderr, end="", file=sys.stderr, flush=True)
    return result.stdout


def _so_minos(so: Path) -> str:
    output = subprocess.check_output(["otool", "-l", str(so)], text=True)
    lines = output.splitlines()
    for index, line in enumerate(lines):
        if "LC_BUILD_VERSION" not in line:
            continue
        for follow in lines[index : index + 10]:
            match = re.search(r"\bminos\s+(\d+\.\d+)", follow)
            if match:
                return match.group(1)
    raise SystemExit(f"无法从 {so} 读取 LC_BUILD_VERSION/minos")


def _so_arch(so: Path) -> str:
    archs = set(subprocess.check_output(["lipo", "-archs", str(so)], text=True).split())
    if archs == {"arm64"}:
        return "arm64"
    if archs == {"x86_64"}:
        return "x86_64"
    if archs == {"arm64", "x86_64"}:
        return "universal2"
    raise SystemExit(f"不支持的架构组合: {sorted(archs)}")


def _python_abi(extension: Path) -> tuple[str, str]:
    # macOS: _core.cpython-311-darwin.so
    # Linux: _core.cpython-311-x86_64-linux-gnu.so
    # Windows: _core.cp311-win_amd64.pyd
    match = re.search(r"\.cpython-(\d+)(\d+)(t?)-[^.]+\.so$", extension.name)
    if match is None:
        match = re.search(r"\.cp(\d+)(\d+)(t?)-[^.]+\.pyd$", extension.name)
    if match is None:
        raise SystemExit(f"无法从文件名推导 Python/ABI tag: {extension.name}")
    python_tag = f"cp{match.group(1)}{match.group(2)}"
    return python_tag, f"{python_tag}{match.group(3)}"


def _platform_tag(minos: str, arch: str) -> str:
    # pip/packaging 的 macOS 兼容标签只按 major.0 枚举；带 minor 的标签
    # （如 macosx_13_3）在更高系统上不会被接受，因此向上取整到下一个 major。
    major, minor = (int(part) for part in minos.split(".", 1))
    if minor > 0:
        major += 1
    return f"macosx_{major}_0_{arch}"


def _find_wheels(paths: list[Path]) -> list[Path]:
    wheels: list[Path] = []
    for path in paths:
        if path.is_dir():
            wheels.extend(sorted(path.glob("*.whl")))
        elif path.suffix == ".whl" and path.is_file():
            wheels.append(path)
        else:
            raise SystemExit(f"不是 wheel 或目录: {path}")
    if not wheels:
        raise SystemExit("没有找到 wheel")
    return wheels


def _retag(wheel: Path) -> Path:
    """macOS：按扩展的实际 minos/架构重写 wheel tag。"""
    with tempfile.TemporaryDirectory() as tmp:
        with zipfile.ZipFile(wheel) as archive:
            members = [name for name in archive.namelist() if name.endswith(".so")]
            if len(members) != 1:
                raise SystemExit(f"{wheel.name} 中应恰好有一个 .so，实际: {members}")
            archive.extract(members[0], tmp)
            so = Path(tmp) / members[0]

        minos = _so_minos(so)
        arch = _so_arch(so)
        python_tag, abi_tag = _python_abi(so)
        platform_tag = _platform_tag(minos, arch)

    expected = f"{python_tag}-{abi_tag}-{platform_tag}"
    with zipfile.ZipFile(wheel) as archive:
        wheel_meta = next(name for name in archive.namelist() if name.endswith(".dist-info/WHEEL"))
        current = archive.read(wheel_meta).decode()
    if f"Tag: {expected}" in current:
        print(f"{wheel.name} 已是 {expected}，跳过", flush=True)
        return wheel

    if importlib.util.find_spec("wheel") is None:
        raise SystemExit("需要 wheel 包：python -m pip install wheel")

    output = _run(
        [
            sys.executable,
            "-m",
            "wheel",
            "tags",
            "--remove",
            "--python-tag",
            python_tag,
            "--abi-tag",
            abi_tag,
            "--platform-tag",
            platform_tag,
            str(wheel),
        ]
    )
    new_wheel = Path(output.strip().splitlines()[-1])
    if not new_wheel.is_file():
        # wheel tags 在输入为相对路径时只回显文件名，新文件与旧文件同目录。
        new_wheel = wheel.parent / new_wheel.name
    with zipfile.ZipFile(new_wheel) as archive:
        wheel_meta = next(name for name in archive.namelist() if name.endswith(".dist-info/WHEEL"))
        text = archive.read(wheel_meta).decode()
    if f"Tag: {expected}" not in text:
        raise SystemExit(f"{new_wheel.name} 的 WHEEL 缺少 Tag: {expected}:\n{text}")

    print(f"{wheel.name} -> {new_wheel.name} (minos {minos}, {arch})", flush=True)
    return new_wheel


def _linux_retag(wheel: Path, spec: SdkPlatform) -> Path:
    """Linux：用 auditwheel 修成 manylinux_2_28，并删掉未修的输入 wheel。"""
    if shutil.which("auditwheel") is None:
        raise SystemExit("需要 auditwheel：python -m pip install auditwheel")

    fixed_dir = wheel.parent / "_fixed"
    fixed_dir.mkdir(exist_ok=True)
    for stale in fixed_dir.glob("*.whl"):
        stale.unlink()

    _run(
        [
            sys.executable,
            "-m",
            "auditwheel",
            "repair",
            "--plat",
            spec.wheel_platform,
            "--only-plat",
            "--wheel-dir",
            str(fixed_dir),
            str(wheel),
        ]
    )
    fixed = sorted(fixed_dir.glob("*.whl"))
    if len(fixed) != 1:
        raise SystemExit(f"auditwheel 应产出一个 wheel，实际: {fixed}")

    target = wheel.parent / fixed[0].name
    if target.exists() and target != wheel:
        target.unlink()
    shutil.move(str(fixed[0]), target)
    if wheel != target and wheel.exists():
        wheel.unlink()
    _run([sys.executable, "-m", "auditwheel", "show", str(target)])
    return target


def _windows_check(wheel: Path) -> Path:
    """Windows：校验 win_amd64 标签与唯一的 yunpyopt/_core*.pyd。"""
    expected = "cp311-cp311-win_amd64"
    if f"-{expected}.whl" not in wheel.name:
        raise SystemExit(f"Windows wheel 标签不正确: {wheel.name}")

    with zipfile.ZipFile(wheel) as archive:
        members = [name for name in archive.namelist() if name.endswith(".pyd")]
        wheel_meta = next(name for name in archive.namelist() if name.endswith(".dist-info/WHEEL"))
        text = archive.read(wheel_meta).decode()

    if len(members) != 1 or not members[0].startswith("yunpyopt/_core."):
        raise SystemExit(f"{wheel.name} 中应恰好有一个 yunpyopt/_core*.pyd，实际: {members}")
    if f"Tag: {expected}" not in text:
        raise SystemExit(f"{wheel.name} 的 WHEEL 缺少 Tag: {expected}:\n{text}")
    return wheel


def main() -> None:
    parser = argparse.ArgumentParser(description="按平台修正/校验 wheel 平台标签")
    parser.add_argument("paths", nargs="*", type=Path, default=[Path("dist")])
    args = parser.parse_args()

    spec = detect_platform()
    for wheel in _find_wheels(args.paths):
        if spec.system == "darwin":
            _retag(wheel)
        elif spec.system == "linux":
            _linux_retag(wheel, spec)
        else:
            _windows_check(wheel)


if __name__ == "__main__":
    main()
