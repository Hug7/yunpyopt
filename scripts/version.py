#!/usr/bin/env python3
"""统一版本管理：读取、校验与升级 yunpyopt 的版本号。

版本真源是仓库根目录的 ``VERSION``（单行 ``X.Y.Z``）。``pyproject.toml`` 的 version
是 poetry-core 构建时需要的静态副本，由本脚本改写并由 ``check`` 校验；
``yun-sdk-version.txt`` 是外部 yun SDK 的依赖 pin，major.minor 必须与包版本一致。
规则见 ``docs/versioning.md``。

用法::

    python scripts/version.py show
    python scripts/version.py check
    python scripts/version.py bump patch
    python scripts/version.py set 0.4.0
"""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+$")
TAG_RE = re.compile(r"^v(\d+\.\d+\.\d+)$")
PYPROJECT_VERSION_RE = re.compile(r'(?m)^version = "[^"]*"$')
DOC_HARDCODE_RULES = (
    (re.compile(r"yunpyopt-(\d+\.\d+\.\d+)-"), "改用 yunpyopt-<version>-..."),
    (re.compile(r"releases/download/v(\d+\.\d+\.\d+)/"), "改用 releases/download/v<version>/..."),
    (re.compile(r"poetry version (\d+\.\d+\.\d+)"), "改用 python scripts/version.py bump/set"),
)


class VersionError(RuntimeError):
    """版本文件或派生位置不可用。"""


def _validate(version: str) -> None:
    if not SEMVER_RE.fullmatch(version):
        raise VersionError(f"版本号非法（应为 X.Y.Z）: {version!r}")


def read_version(root: Path = ROOT) -> str:
    path = root / "VERSION"
    if not path.is_file():
        raise VersionError(f"缺少版本文件: {path}")
    version = path.read_text(encoding="utf-8").strip()
    _validate(version)
    return version


def read_sdk_version(root: Path = ROOT) -> str:
    path = root / "yun-sdk-version.txt"
    if not path.is_file():
        raise VersionError(f"缺少 SDK pin: {path}")
    version = path.read_text(encoding="utf-8").strip()
    _validate(version)
    return version


def _pyproject_version(root: Path) -> str:
    path = root / "pyproject.toml"
    try:
        data = tomllib.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise VersionError(f"缺少 {path}") from None
    except tomllib.TOMLDecodeError as exc:
        raise VersionError(f"{path} 解析失败: {exc}") from exc
    try:
        value = data["tool"]["poetry"]["version"]
    except (KeyError, TypeError):
        raise VersionError(f"{path}: 缺少 [tool.poetry] version") from None
    if not isinstance(value, str):
        raise VersionError(f"{path}: [tool.poetry] version 必须是字符串")
    return value


def _major_minor(version: str) -> tuple[int, int]:
    major, minor = version.split(".")[:2]
    return int(major), int(minor)


def _doc_files(root: Path) -> list[Path]:
    candidates = [root / "README.md"]
    docs = root / "docs"
    if docs.is_dir():
        candidates += sorted(docs.rglob("*.md"))
    return [
        path
        for path in candidates
        if path.is_file() and path.name != "CHANGELOG.md" and "superpowers" not in path.relative_to(root).parts
    ]


def _head_tag(root: Path) -> str | None:
    try:
        result = subprocess.run(
            ["git", "-C", str(root), "describe", "--tags", "--exact-match", "HEAD"],
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError:
        return None
    if result.returncode != 0:
        return None
    return result.stdout.strip() or None


def _tag(root: Path) -> str | None:
    ref = os.environ.get("GITHUB_REF", "")
    if ref.startswith("refs/tags/"):
        return os.environ.get("GITHUB_REF_NAME") or ref.removeprefix("refs/tags/")
    return _head_tag(root)


def check(root: Path = ROOT) -> list[str]:
    """返回不一致项；空列表表示通过。"""
    try:
        version = read_version(root)
    except VersionError as exc:
        return [str(exc)]

    problems: list[str] = []

    try:
        package_version = _pyproject_version(root)
    except VersionError as exc:
        problems.append(str(exc))
    else:
        if package_version != version:
            problems.append(
                f"pyproject.toml: version={package_version} 与 VERSION={version} 不一致；"
                "运行 python scripts/version.py set <version> 同步"
            )

    try:
        sdk_version = read_sdk_version(root)
    except VersionError as exc:
        problems.append(str(exc))
    else:
        if _major_minor(sdk_version) != _major_minor(version):
            problems.append(f"yun-sdk-version.txt: SDK {sdk_version} 的 major.minor 必须与包版本 {version} 一致")

    workflow_path = root / ".github" / "workflows" / "release.yml"
    if not workflow_path.is_file():
        problems.append("缺少 .github/workflows/release.yml")
    else:
        workflow = workflow_path.read_text(encoding="utf-8")
        if "scripts/version.py check" not in workflow:
            problems.append("release.yml: version job 应调用 scripts/version.py check")
        for hardcoded in sorted(set(re.findall(r"\b\d+\.\d+\.\d+\b", workflow))):
            problems.append(f"release.yml: 硬编码版本 {hardcoded}；版本应来自 VERSION")

    for path in _doc_files(root):
        rel = path.relative_to(root)
        for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            for pattern, hint in DOC_HARDCODE_RULES:
                found = pattern.search(line)
                if found is not None:
                    problems.append(f"{rel}:{lineno}: 硬编码版本 {found.group(1)}（{hint}）")

    changelog = root / "CHANGELOG.md"
    if not changelog.is_file():
        problems.append("缺少 CHANGELOG.md")
    elif f"## [{version}]" not in changelog.read_text(encoding="utf-8"):
        problems.append(f"CHANGELOG.md: 缺少 '## [{version}]' 段落")

    tag = _tag(root)
    if tag is not None:
        match = TAG_RE.fullmatch(tag)
        if match is None:
            problems.append(f"git tag {tag} 不是 vX.Y.Z 格式")
        elif match.group(1) != version:
            problems.append(f"git tag {tag} 与 VERSION {version} 不一致")

    return problems


def next_version(current: str, part: str) -> str:
    major, minor, patch = (int(component) for component in current.split("."))
    if part == "major":
        return f"{major + 1}.0.0"
    if part == "minor":
        return f"{major}.{minor + 1}.0"
    return f"{major}.{minor}.{patch + 1}"


def _write_version(root: Path, version: str) -> None:
    (root / "VERSION").write_text(f"{version}\n", encoding="utf-8")


def _write_pyproject_version(root: Path, version: str) -> None:
    path = root / "pyproject.toml"
    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        raise VersionError(f"缺少 {path}") from None
    updated, count = PYPROJECT_VERSION_RE.subn(f'version = "{version}"', text)
    if count != 1:
        raise VersionError(f'{path}: 应有且仅有一处顶层 version = "..."（实际 {count} 处）')
    path.write_text(updated, encoding="utf-8")


def set_version(version: str, root: Path = ROOT) -> None:
    _validate(version)
    _write_version(root, version)
    _write_pyproject_version(root, version)


def _print_next_steps(version: str, root: Path) -> None:
    print("后续步骤：")
    print(f"  1. 在 CHANGELOG.md 记录 {version} 的变更")
    try:
        sdk_version = read_sdk_version(root)
    except VersionError:
        pass
    else:
        if _major_minor(sdk_version) != _major_minor(version):
            print(f"  2. yun-sdk-version.txt 仍是 {sdk_version}：SDK major.minor 变化时需同步更新 pin")
    print(f'  3. git tag -a v{version} -m "yunpyopt {version}"（推送前需人工批准）')


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="yunpyopt 统一版本管理")
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("show", help="打印当前版本")
    subparsers.add_parser("check", help="校验所有派生位置（CI 使用）")
    bump = subparsers.add_parser("bump", help="升级版本并同步 pyproject.toml")
    bump.add_argument("part", choices=["major", "minor", "patch"])
    set_parser = subparsers.add_parser("set", help="直接设置版本")
    set_parser.add_argument("version", help="目标版本（X.Y.Z）")
    args = parser.parse_args(argv)

    try:
        if args.command == "show":
            print(read_version(ROOT))
        elif args.command == "check":
            problems = check(ROOT)
            for problem in problems:
                print(f"✗ {problem}", file=sys.stderr)
            if problems:
                print(
                    f"\n版本校验失败：{len(problems)} 处不一致；按提示修正后重新运行。",
                    file=sys.stderr,
                )
                return 1
            print(f"版本校验通过：{read_version(ROOT)}")
        elif args.command == "set":
            set_version(args.version, root=ROOT)
            print(f"版本已设置为 {args.version}")
            _print_next_steps(args.version, ROOT)
        elif args.command == "bump":
            current = read_version(ROOT)
            version = next_version(current, args.part)
            set_version(version, root=ROOT)
            print(f"版本 {current} -> {version}")
            _print_next_steps(version, ROOT)
    except VersionError as exc:
        print(f"错误：{exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
