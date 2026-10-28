"""下载并解压 yun Release 的预编译 SDK。

优先级：
1. ``YUN_SDK_DIR``：本地已解压的 SDK 目录（开发/离线）
2. ``YUN_SDK_CACHE`` 下的缓存（默认 ``~/.cache/yunpyopt/sdk``）
3. 从 ``yun-sdk-version.txt``（或 ``YUN_SDK_VERSION``）对应的 GitHub Release 下载

下载后会用 Release 附带的 ``SHA256SUMS`` 校验；也可用 ``YUN_SDK_SHA256`` 直接指定。
可选的 ``YUN_SDK_URL`` 用于覆盖下载地址（测试/镜像）。
"""

from __future__ import annotations

import argparse
import hashlib
import os
import platform
import shutil
import sys
import tarfile
import tempfile
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VERSION_FILE = ROOT / "yun-sdk-version.txt"
RELEASE_BASE = "https://github.com/Hug7/yun/releases/download"
DEFAULT_CACHE = Path.home() / ".cache" / "yunpyopt" / "sdk"


def resolve_version() -> str:
    version = os.environ.get("YUN_SDK_VERSION")
    if not version:
        if not VERSION_FILE.is_file():
            raise SystemExit(f"缺少 {VERSION_FILE}；请写入 yun SDK 版本")
        version = VERSION_FILE.read_text().strip()
    if not version:
        raise SystemExit(f"{VERSION_FILE} 为空")
    return version


def sdk_name(version: str) -> str:
    machine = platform.machine()
    if machine not in {"arm64", "x86_64"}:
        raise SystemExit(f"不支持的 macOS 架构: {machine}")
    arch = "arm64" if machine == "arm64" else "x86_64"
    return f"yun-sdk-{version}-macos-{arch}.tar.gz"


def sdk_url(version: str) -> str:
    explicit = os.environ.get("YUN_SDK_URL")
    if explicit:
        return explicit
    return f"{RELEASE_BASE}/v{version}/{sdk_name(version)}"


def _download(url: str, destination: Path) -> None:
    print(f"下载 {url}", flush=True)
    try:
        with urllib.request.urlopen(url, timeout=120) as response, destination.open("wb") as target:
            shutil.copyfileobj(response, target)
    except Exception as exc:  # noqa: BLE001 - 给出可操作的提示
        raise SystemExit(
            f"下载失败: {url}\n{exc}\n"
            "如果 yun 还没有发布对应版本的 SDK，请先运行 yun 的 SDK Release workflow；"
            "本地开发可设置 YUN_SDK_DIR 指向已解压的 SDK。"
        ) from exc


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _expected_sha256(version: str, name: str) -> str:
    explicit = os.environ.get("YUN_SDK_SHA256")
    if explicit:
        return explicit.strip().lower()

    checksums_url = os.environ.get("YUN_SDK_SHA256SUMS_URL") or f"{RELEASE_BASE}/v{version}/SHA256SUMS"
    with tempfile.TemporaryDirectory() as tmp:
        checksums = Path(tmp) / "SHA256SUMS"
        _download(checksums_url, checksums)
        for line in checksums.read_text().splitlines():
            parts = line.split()
            if len(parts) == 2 and parts[1].lstrip("*") == name:
                return parts[0].lower()
    raise SystemExit(f"SHA256SUMS 中找不到 {name}")


def _extract(archive: Path, destination: Path) -> None:
    destination.mkdir(parents=True, exist_ok=True)
    with tarfile.open(archive, "r:gz") as tar:
        try:
            tar.extractall(destination, filter="data")
        except TypeError:  # Python < 3.11.4
            tar.extractall(destination)


def ensure_sdk(version: str | None = None) -> Path:
    local = os.environ.get("YUN_SDK_DIR")
    if local:
        path = Path(local).expanduser().resolve()
        if not (path / "lib" / "libyun_sdk.a").is_file():
            raise SystemExit(f"YUN_SDK_DIR={path} 不是有效的 yun SDK（缺少 lib/libyun_sdk.a）")
        return path

    version = version or resolve_version()
    name = sdk_name(version)
    cache_root = Path(os.environ.get("YUN_SDK_CACHE", DEFAULT_CACHE)).expanduser()
    target = cache_root / version
    marker = target / "lib" / "libyun_sdk.a"
    if marker.is_file():
        return target

    with tempfile.TemporaryDirectory() as tmp:
        archive = Path(tmp) / name
        _download(sdk_url(version), archive)
        actual = _sha256(archive)
        expected = _expected_sha256(version, name)
        if actual != expected:
            raise SystemExit(f"SDK 校验失败：expected={expected}, actual={actual}\n文件: {archive}")
        print(f"SDK sha256 ok: {actual}", flush=True)
        _extract(archive, target)

    if not marker.is_file():
        raise SystemExit(f"SDK 解压后缺少 lib/libyun_sdk.a: {target}")
    return target


def main() -> None:
    parser = argparse.ArgumentParser(description="获取 yun 预编译 SDK")
    parser.add_argument("--version", default=None, help="SDK 版本（默认读 yun-sdk-version.txt）")
    args = parser.parse_args()
    print(ensure_sdk(args.version))


if __name__ == "__main__":
    sys.exit(main())
