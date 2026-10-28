#!/usr/bin/env python3
"""修正 wheel 的平台标签，使其与扩展二进制的实际 minos 一致。

poetry-core 用构建解释器的 ``sys_tags``（例如 ``macosx_11_0_arm64``）作为 wheel
标签，但 yun 的 C++20 ``std::format`` 需要 macOS 13.3+，扩展的实际 minos 更高。
由于 pip 的 macOS 兼容标签按 ``major.0`` 枚举（``macosx_13_3`` 在更高系统上不会被
接受），本脚本把 minos 向上取整到下一个 major（13.3 -> 14_0），再读取
``LC_BUILD_VERSION/minos`` 与 ``lipo`` 架构，调用 ``wheel tags`` 重写文件名、WHEEL 与 RECORD。
"""

from __future__ import annotations

import argparse
import importlib.util
import re
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path


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


def _python_abi(so: Path) -> tuple[str, str]:
    match = re.search(r"\.cpython-(\d+)(\d+)(t?)-darwin\.so$", so.name)
    if not match:
        raise SystemExit(f"无法从文件名推导 Python/ABI tag: {so.name}")
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


def main() -> None:
    parser = argparse.ArgumentParser(description="把 wheel 平台标签修正为扩展的实际 minos")
    parser.add_argument("paths", nargs="*", type=Path, default=[Path("dist")])
    args = parser.parse_args()
    for wheel in _find_wheels(args.paths):
        _retag(wheel)


if __name__ == "__main__":
    main()
