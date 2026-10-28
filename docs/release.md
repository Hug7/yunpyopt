# Release 手册

本项目的发布物是 **GitHub Release 上的 macOS arm64 wheel**（暂不发 PyPI）。
版本号以 `pyproject.toml` 为准，tag 必须严格等于 `v<version>`（例如 `v0.1.0`）。

`yunpyopt` 不再通过 submodule 拉取 `yun` 源码，而是消费 `yun` Release 上的
**预编译 SDK**（headers + 单体静态库 + binding 源码），版本由
[`yun-sdk-version.txt`](../yun-sdk-version.txt) 固定。

## 前置条件

- `yun` 的 SDK Release 已发布，附件包含：
  - `yun-sdk-<version>-macos-arm64.tar.gz`
  - `SHA256SUMS`
- 两个仓库都是 public；GitHub Actions 的 `macos-14` runner 可用。
- `yunpyopt` 本地：macOS 14+ arm64、Xcode CLT、CMake ≥ 3.15、Python 3.11、Poetry。
  （`yunpyopt` 不再需要 Conan；Conan 只在构建 `yun` SDK 时需要。）

## 1. 发布 `yun` SDK

1. 合并 `yun` 的 packaging 分支到 `main`。
2. 触发 `yun` 的 **SDK Release** workflow：
   - 先 `workflow_dispatch`（`version=0.1.0`）演练，确认 tarball 与 `SHA256SUMS`；
   - 再 push tag `v0.1.0`，生成 GitHub Release。
3. 确认 Release 附件：

   ```text
   yun-sdk-0.1.0-macos-arm64.tar.gz
   SHA256SUMS
   ```

4. **不要覆盖已发布版本的 SDK**。C++ 有变化时 bump SDK 版本并重新发布。

## 2. 更新 `yunpyopt` 的 SDK pin

如果 SDK 版本变化：

```bash
echo 0.1.0 > yun-sdk-version.txt
```

本地验收（默认会从 GitHub Release 下载并校验；也可用本地 SDK）：

```bash
# 可选：本地 SDK
export YUN_SDK_DIR=/path/to/yun-sdk

poetry install
YUNPYOPT_REQUIRE_CORE=1 poetry run pytest -v
poetry run ruff check src tests scripts
poetry run ruff format --check src tests scripts
poetry run mypy src
poetry build -f wheel
poetry run python scripts/fix_wheel_tag.py dist
```

期望 wheel：

```text
dist/yunpyopt-0.2.0-cp311-cp311-macosx_14_0_arm64.whl
```

`fetch_sdk.py` 会下载 `SHA256SUMS` 并校验 tarball；如需用测试镜像，可设置
`YUN_SDK_URL` / `YUN_SDK_SHA256`（仅用于调试，正式发布不要依赖覆盖值）。

## 3. 升版本

```bash
poetry version 0.2.0          # 或者手工改 pyproject.toml 的 [tool.poetry].version
poetry lock                    # 版本变化后同步 lock 的 content-hash
```

更新 `CHANGELOG.md`（记录本次使用的 SDK 版本），然后提交：

```bash
git add pyproject.toml poetry.lock CHANGELOG.md yun-sdk-version.txt
git commit -m "chore(release): v0.2.0"
```

## 4. 先做一次手动演练

在 GitHub Actions 里运行 **Release → Run workflow**（`workflow_dispatch`）：

- 会下载 SDK、构建 wheel、修正标签、跑冒烟测试、上传 artifact；
- **不会**创建 Release（只有 `v*` tag 才会）。

从 artifact 下载 wheel，在干净环境复验：

```bash
python3.11 -m venv /tmp/yunpyopt-check
/tmp/yunpyopt-check/bin/pip install /path/to/yunpyopt-0.2.0-cp311-cp311-macosx_14_0_arm64.whl
cp -R tests/data/c1_2_1 /tmp/c1_2_1
/tmp/yunpyopt-check/bin/python -c "
from pathlib import Path
from yunpyopt import solve
r = solve('/tmp/c1_2_1', log_level='warning')
assert r['loads'] and Path(r['loads']).is_file(), r
print(r)
"
```

## 5. 正式发布

```bash
git push origin main
git tag v0.2.0
git push origin v0.2.0
```

`Release` workflow 会：

1. 校验 tag 与 `pyproject.toml` 版本一致；
2. 下载 `yun-sdk-version.txt` 对应的 SDK（校验 SHA256）；
3. 构建 wheel 并修正平台标签；
4. `twine check` + 干净 venv 安装 + 真实求解；
5. 校验 `otool -L` 只依赖系统库、且没有 `LC_RPATH`；
6. 创建 GitHub Release，附件为
   `yunpyopt-0.2.0-cp311-cp311-macosx_14_0_arm64.whl`。

安装方式：

```bash
pip install https://github.com/Hug7/yunpyopt/releases/download/v0.2.0/yunpyopt-0.2.0-cp311-cp311-macosx_14_0_arm64.whl
```

## 6. 回滚

- 在 GitHub 上把 Release 改为 draft 或删除；
- 删除 tag 后重打，**不要复用已发布的版本号**；
- 若 SDK 有问题，回退 `yun-sdk-version.txt` 到上一个可用版本并重新发布。

## 7. 依赖顺序（硬约束）

1. 先发布 `yun` 的 SDK Release（`v<yun-version>`）；
2. 再更新 `yunpyopt` 的 `yun-sdk-version.txt` 并 push；
3. 最后打 `yunpyopt` 的 tag。

`yunpyopt` 的 CI/Release 会从 `https://github.com/Hug7/yun/releases/download/v<version>/`
下载 SDK；SDK 不存在时构建会直接失败。`SHA256SUMS` 保证下载内容与 release 一致。

## 8. 后续：PyPI

本阶段不发布 PyPI。以后需要时，在 `release.yml` 增加一个 publish job：

```yaml
  publish:
    needs: build
    runs-on: ubuntu-latest
    environment: pypi
    permissions:
      id-token: write
    steps:
      - uses: actions/download-artifact@v4
        with:
          name: wheel
          path: dist
      - uses: pypa/gh-action-pypi-publish@release/v1
```

并在 PyPI 配置 Trusted Publisher（repo `Hug7/yunpyopt`、workflow `release.yml`、
environment `pypi`）。
