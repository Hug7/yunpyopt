# 变更日志

本文件记录项目所有值得注意的变更。

格式基于 [Keep a Changelog](https://keepachangelog.com/en/1.1.0/)，
版本号遵循 [语义化版本](https://semver.org/spec/v2.0.0.html)。

## [0.3.0] — Unreleased

### 变更（Changed）

- 版本号统一由根目录 `VERSION` 管理：新增 `scripts/version.py`（`show` / `check` /
  `set` / `bump`），`pyproject.toml` 由脚本同步，CI 与 Release 通过 `check` 校验
  `VERSION`、包版本、SDK pin 与 tag；README/docs 不再写死当前版本
- `yun-sdk-version.txt` 升级到 `0.3.1`（patch，不强制升级包版本）
- `yun-sdk-version.txt` 升级到 `0.3.0`，`yunpyopt` 版本同步升级到 `0.3.0`；
  `yun` SDK 0.3.0 与 0.2.0 ABI 不兼容，扩展需重新构建
- 新增版本策略：`yun` SDK 的 major.minor 变化时，`yunpyopt` 的 major.minor 同步升级；patch 变化不强制

## [0.2.0] — Unreleased

### 新增（Added）

- 支持 macOS arm64、Linux x86_64、Linux arm64、Windows x86_64 四个平台的预编译 wheel
- 新增 `plan_summary` 结果（指向 `PlanSummary.json`）
- 新增 `SolveResult` 类型与 Python 版 `Solver` 包装（支持 context manager、`output_dir`）
- 新增 `SDK_VERSION` / `SDK_PLATFORM`，便于定位构建所用 SDK 与平台
- CI 增加四平台构建、安装与求解冒烟

### 变更（Changed）

- `fetch_sdk.py` / `build_ext.py` / `fix_wheel_tag.py` 平台化，支持 `.a`/`.lib`、`.so`/`.pyd`
- Linux wheel 使用 `manylinux_2_28` 标签，并静态链接 `libstdc++`/`libgcc`
- Windows wheel 使用 `win_amd64` 标签，保持 `/MD` 运行时
- Windows 暂不支持非 ASCII 案例路径；检测到后抛出明确的 `ValueError`

### 修复（Fixed）

- 修复 Windows wheel 未包含 `_core*.pyd` 的问题（`*.py[codz]` 误匹配 `.pyd`）
- 修复 Windows 构建脚本在 cp1252 控制台下的中文编码错误
- 修复 Linux wheel 平台标签出现 `manylinux_2_26...manylinux_2_28...` 复合标签的问题
- 修正文档中关于 ALNS 结果导出的过时说明：导出的是 ALNS 最优解，`max_iter` 会影响结果

### 移除（Removed）

- 移除“仅 macOS 14.0+ arm64”的文档与错误提示

## [0.1.0] — Unreleased

### 新增（Added）

- 面向物流优化的领域 schema 数据类：
  - `Dimension`、`Label`、`LabelValue`、`LabelApply`（基础字典）
  - `Location`、`LocationLabelValue`、`LocationAvailableVehicle`、`WorkCalendarDaily`、`WorkCalendarWeekly`、`WorkFixed`、`WorkEffect`（位置）
  - `VehicleModel`、`VehicleModelDimensionValue`、`VehicleModelLabelValue`（车型）
  - `Carrier`、`CarrierLabelValue`、`Vehicle`（承运商）
  - `DistMatrix`（路线网络）
  - `CargoOrder`、`CargoSubOrder`、`CargoSubOrderDimensionValue`、`CargoSubOrderLabelValue`（订单）
- 所有领域模型提供简洁的 `__repr__`
- 通过 `importlib.metadata` 提供包级 `__version__`
- 提供 `py.typed` 标记，符合 PEP 561
- 新增 `typing-extensions` 运行时依赖（用于 Python 3.11 的 `typing.override`）
- 新增 `yunpyopt.solver.solve()` / `Solver`，用于进程内调用 `yun` 求解器
- `from yunpyopt import solve` 采用懒加载，只用领域模型的用户无需二进制扩展
- 新增 `tests/data/c1_2_1` 夹具与求解器集成测试
- 新增 PEP 517 构建钩子（`scripts/build_ext.py`）：下载固定版本的预编译 `yun` SDK
  （头文件 + 单体静态库 + binding 源码），并用 pybind11 构建 `yunpyopt._core`
- 新增 `scripts/fetch_sdk.py`，用于下载、校验并缓存 SDK（`SHA256SUMS`）
- 新增 `scripts/fix_wheel_tag.py`，按扩展的实际 `LC_BUILD_VERSION` minos 修正 wheel 平台标签
- 新增 GitHub Actions CI（macOS arm64、CPython 3.11），覆盖 lint、类型检查、扩展构建、
  测试、wheel 构建/校验与 clean venv 安装/求解
- 新增 `release.yml`：按 tag 构建 wheel 并创建 GitHub Release（暂未启用 PyPI 发布）

### 变更（Changed）

- `yun` SDK 版本固定在 `yun-sdk-version.txt`；`yunpyopt` 不再需要 `yun` 源码 checkout 或 Conan
- wheel 使用平台标签（`cp311-cp311-macosx_14_0_arm64`），不再是 `py3-none-any`
- 支持平台为 macOS 14.0+ arm64、CPython 3.11（C++ 代码使用 `std::format`，需要
  macOS 13.3；由于 pip 的 macOS 标签按 major 版本枚举，wheel 标签向上取整为 14_0）
- `solver.solve()` 支持 `PathLike`，会按 binding 校验结果 key；缺少 `yunpyopt._core` 时
  抛出清晰的 `ImportError`
- 更新 lint/类型检查配置；`ruff` 与 `mypy` 通过

### 移除（Removed）

- 移除 `yun` git submodule（`third_party/yun`）
- 移除 `yun` 的 `BUILD_PY.sh`（硬编码 `python3.11` 和旧的 `yunpy` 输出路径）；
  改用 `yun/scripts/build_python_extension.py`
