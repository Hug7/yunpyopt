# Release 手册

本项目的发布物是 **GitHub Release 上的四个平台 wheel**（PyPI 暂未启用）：

```text
yunpyopt-0.2.0-cp311-cp311-macosx_14_0_arm64.whl
yunpyopt-0.2.0-cp311-cp311-manylinux_2_28_x86_64.whl
yunpyopt-0.2.0-cp311-cp311-manylinux_2_28_aarch64.whl
yunpyopt-0.2.0-cp311-cp311-win_amd64.whl
```

版本号以 `pyproject.toml` 为准，tag 必须严格等于 `<version>`（例如 `0.2.0`）。
`yunpyopt` 消费 `yun` Release 上的**预编译 SDK**，版本由
[`yun-sdk-version.txt`](../yun-sdk-version.txt) 固定。

## 前置条件

- `yun` 的 SDK Release 已发布，附件包含四个 tarball 与 `SHA256SUMS`：

  ```text
  yun-sdk-0.2.0-macos-arm64.tar.gz
  yun-sdk-0.2.0-linux-x86_64.tar.gz
  yun-sdk-0.2.0-linux-arm64.tar.gz
  yun-sdk-0.2.0-windows-x86_64.tar.gz
  SHA256SUMS
  ```

- 若 `yun` Release 仍是 prerelease，先转为稳定版（或在 release notes 明确依赖 prerelease）；
- 两个仓库都是 public；
- GitHub Actions 可用的 runner：`macos-15`、`ubuntu-24.04`、`ubuntu-24.04-arm`、
  `windows-2022`；
- 本地复验环境：对应平台的 Python 3.11；Linux 建议 `manylinux_2_28` 容器。

## 1. 确认 yun SDK

在 `yun` 仓库确认 `project(yun VERSION ...)` 与 `yun-sdk-version.txt` 一致，且四个资产可下载：

```bash
curl -sS https://api.github.com/repos/Hug7/yun/releases/tags/v0.2.0 \
  | python -c 'import json,sys; print("\n".join(a["name"] for a in json.load(sys.stdin)["assets"]))'
```

不要在 `yunpyopt` 中覆盖已发布 SDK 的 `SHA256SUMS`；C++ 变更时 bump `yun` 版本并发布新 SDK。

## 2. 更新版本与 pin

```bash
poetry version 0.2.0
poetry lock
```

如果 SDK 版本变化：

```bash
echo 0.2.0 > yun-sdk-version.txt
```

更新 `CHANGELOG.md`（0.2.0 条目；中文规范见 Task 11），然后本地校验：

```bash
poetry check --lock
poetry run ruff check src tests scripts
poetry run ruff format --check src tests scripts
poetry run mypy src
YUNPYOPT_REQUIRE_CORE=1 poetry run pytest -v
```

## 3. 本地构建与验收

### macOS arm64

```bash
YUN_SDK_DIR=/path/to/yun-sdk-0.2.0-macos-arm64 poetry install
poetry build -f wheel
poetry run python scripts/fix_wheel_tag.py dist
ls dist/*.whl
```

期望：`yunpyopt-0.2.0-cp311-cp311-macosx_14_0_arm64.whl`。

### Linux x86_64 / arm64

在 `quay.io/pypa/manylinux_2_28_x86_64` / `..._aarch64` 容器内：

```bash
source /opt/rh/gcc-toolset-14/enable
PY=/opt/python/cp311-cp311/bin/python
export PATH="$(dirname "$PY"):$PATH"
export CC="$(command -v gcc)" CXX="$(command -v g++)"

"$PY" -m pip install build twine wheel auditwheel
"$PY" -m build --wheel --outdir dist
"$PY" scripts/fix_wheel_tag.py dist
```

期望：`manylinux_2_28_x86_64` / `manylinux_2_28_aarch64` 标签，且
`auditwheel show` 通过、无外部 `libstdc++`。

### Windows x64

在 VS 2022 开发者环境（含 LLVM/clang-cl、Ninja）中：

```bat
python -m pip install build twine wheel ninja
python -m build --wheel --outdir dist
python scripts\fix_wheel_tag.py dist
```

期望：`yunpyopt-0.2.0-cp311-cp311-win_amd64.whl`，`dumpbin /dependents` 只包含约定的
系统/运行库 DLL。

### wheel 安装冒烟（每个平台）

```bash
python -m venv /tmp/yunpyopt-check
/tmp/yunpyopt-check/bin/pip install dist/*.whl
cp -R tests/data/c1_2_1 /tmp/c1_2_1
rm -rf /tmp/c1_2_1/output
/tmp/yunpyopt-check/bin/python - <<'PY'
from pathlib import Path
from yunpyopt import solve
r = solve('/tmp/c1_2_1', log_level='warning')
assert r['loads'] and Path(r['loads']).is_file(), r
assert r['plan_summary'] and Path(r['plan_summary']).is_file(), r
print(r)
PY
```

Windows 用 `.venv\Scripts\python.exe` 等价路径。

## 4. 先做一次手动演练

在 GitHub Actions 运行 **Release → Run workflow**（`workflow_dispatch`）：

- `version` job 校验 `yun-sdk-version.txt`；
- 四个 build job 构建、修标签、冒烟、上传 artifact；
- **不会**创建 Release（只有 `v*` tag 才创建）。

从 artifact 下载四个 wheel，逐个在对应平台/容器安装并跑上面的冒烟；确认：

- 四个平台 `YUNPYOPT_REQUIRE_CORE=1 pytest` 全绿；
- `plan_summary` 有值；
- Linux `auditwheel show`、Windows `dumpbin`、macOS `otool` 检查通过；
- `CHANGELOG.md` 已中文化并覆盖 0.2.0。

## 5. 正式发布

```bash
git push origin main
git tag v0.2.0
git push origin v0.2.0
```

`Release` workflow 会：

1. 校验 tag 与 `pyproject.toml` 版本、SDK pin；
2. 构建四个平台 wheel；
3. 下载 artifact，校验恰好四个 wheel 与命名；
4. 生成 `SHA256SUMS`；
5. 创建 GitHub Release，附件为四个 wheel + `SHA256SUMS`。

安装方式见 [README](../README.md#install)。

## 6. 回滚

- 在 GitHub 上把 Release 改为 draft 或删除；
- 删除 tag 后重打，**不要复用已发布的版本号**；
- 若 SDK 有问题，回退 `yun-sdk-version.txt` 到上一个可用版本并重新发布；
- 若某个平台 wheel 有问题，先下架整个 Release，修复后 bump 版本重发。

## 7. 依赖顺序（硬约束）

1. 先发布/提升 `yun` 的 SDK Release（`v<yun-version>`）；
2. 再更新 `yunpyopt` 的 `yun-sdk-version.txt` 并 push；
3. 最后打 `yunpyopt` 的 tag。

SDK 不存在时 `fetch_sdk.py` 会报错并提示先运行 `yun` 的 SDK Release workflow；
`SHA256SUMS` 保证下载内容与 Release 一致。

## 8. 后续：PyPI

本阶段不发布 PyPI。以后需要时，在 `release.yml` 增加 `publish-pypi` job，并在 PyPI 配置
Trusted Publisher（repo `Hug7/yunpyopt`、workflow `release.yml`、environment `pypi`）：

```yaml
  publish-pypi:
    needs: [build-macos, build-linux, build-windows]
    if: startsWith(github.ref, 'refs/tags/v') && vars.PUBLISH_TO_PYPI == 'true'
    runs-on: ubuntu-24.04
    environment: pypi
    permissions:
      id-token: write
    steps:
      - uses: actions/download-artifact@v4
        with:
          pattern: wheel-*
          path: dist
          merge-multiple: true
      - uses: pypa/gh-action-pypi-publish@release/v1
```
