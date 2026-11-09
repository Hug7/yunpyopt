# 版本管理

本文规定 `yunpyopt` 的包版本如何产生、校验与发布；SDK 依赖的 pin 规则见
[AGENTS.md](../AGENTS.md) 第 3 节，发布步骤见 [发布手册](release.md)。

## 1. 版本真源

仓库根目录 `VERSION` 保存一行 `X.Y.Z`，这是唯一需要人工修改的包版本。

| 位置 | 如何取得版本 | 说明 |
| --- | --- | --- |
| `VERSION` | 人工/脚本写入 | 包版本真源 |
| `pyproject.toml` | 由 `scripts/version.py set/bump` 改写 | poetry-core 构建时需要静态版本，无法运行时读文件；`check` 校验两者一致 |
| `scripts/version.py` | 读取 `VERSION` | `show` / `check` / `set` / `bump` 的统一入口 |
| `.github/workflows/release.yml` | 调用 `scripts/version.py check` | workflow 不保存版本字面量；tag 必须等于 `v${VERSION}` |
| `src/yunpyopt/__init__.py` | `importlib.metadata.version("yunpyopt")`，未安装的源码树回退读 `VERSION` | wheel 元数据来自已同步的 `pyproject.toml` |
| `src/yunpyopt/_build_info.py` | 构建时写入 SDK 的 `VERSION` | 构建产物，不提交 |
| `yun-sdk-version.txt` | 人工/脚本写入 | **SDK 依赖 pin**，不是包版本；major.minor 必须与 `VERSION` 一致 |
| README / `docs/` | 不写死当前版本 | wheel 名与下载 URL 使用 `<version>` / `<sdk-version>` 占位符 |
| `CHANGELOG.md` | 人工维护 | 只记录历史与当前待发布版本的变更 |

改包版本时不要手改 `pyproject.toml`，统一走第 3 节的脚本。

## 2. 版本规则

- 包版本使用语义化版本 `MAJOR.MINOR.PATCH`。
- 发布 tag 形如 `vX.Y.Z`，必须与 `VERSION` 完全一致；CI 与 Release 都会校验。
- `yunpyopt` 的 major.minor 必须与 `yun-sdk-version.txt` 的 major.minor 一致。
- SDK 的 major/minor 变化（ABI 断点）时必须同步升级包版本；只变 patch 不强制。
- tag 是发布动作，不是真源：构建需要静态版本，不能从 tag 反推。

## 3. 日常命令

```bash
python scripts/version.py show        # 打印当前版本
python scripts/version.py check       # 校验所有派生位置（CI 会跑）
python scripts/version.py bump patch  # major | minor | patch
python scripts/version.py set 0.4.0
```

`bump` / `set` 会更新 `VERSION` 和 `pyproject.toml`，然后打印后续步骤；脚本不会
自动 commit、打 tag 或 push，也不会改写 `CHANGELOG.md` 与 SDK pin。

发布检查清单：

1. 用 `python scripts/version.py bump minor`（或 `patch`）升级包版本；
2. 在 `CHANGELOG.md` 记录当前版本的变更；
3. 若 SDK 的 major.minor 也变化，更新 `yun-sdk-version.txt` 并重新构建扩展；
4. 本地运行 `python scripts/version.py check` 与完整测试；
5. 走 PR 合入 main；
6. 合并后人工打 tag：`git tag -a "v$(cat VERSION)" -m "yunpyopt $(cat VERSION)"`；
7. push tag 触发 Release（推送需人工批准）。

## 4. 文档写法约定

- 不写“当前版本是 x.y.z”这类会漂移的表述；当前包版本只存在 `VERSION` 里。
- wheel 名写 `yunpyopt-<version>-cp311-...`；下载地址写
  `.../releases/download/v<version>/...`。
- SDK 版本只通过 `yun-sdk-version.txt` 引用；文档中的旧版本号仅用于说明历史 ABI
  差异，不属于当前版本。
- 历史版本只写在 `CHANGELOG.md`。
- `docs/superpowers/**` 不参与版本检查。

## 5. 常见问题

**为什么 `pyproject.toml` 里还有 `version` 字面量？**

poetry-core 在构建 wheel 时必须读到静态版本，不支持从 `VERSION` 文件动态读取。
因此把 `pyproject.toml` 当作派生副本：只由 `scripts/version.py` 改写，
`check` 与 CI 保证它永远不会和 `VERSION` 漂移。

**为什么不把 `yun-sdk-version.txt` 合并进 `VERSION`？**

包版本和 SDK 版本是两个概念：SDK 是外部依赖，pin 可以停在某个 patch，而包版本
可以在同一 major.minor 下独立发 patch。合并后任何 SDK patch 都会被迫触发
`yunpyopt` 发版，也会让“SDK pin 回退”变得困难。两者只需 major.minor 一致。

**`build_ext.py` 为什么还要校验 SDK 版本？**

`YUN_SDK_DIR` 可以指向任意本地 SDK；构建前校验 SDK 自带的 `VERSION` 与
`yun-sdk-version.txt` 一致，避免用错 SDK 却生成看似正常的 `_build_info.py`。
