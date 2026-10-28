# yunpyopt 封装与发布

> 平台：macOS 15.0+（arm64）/ CPython 3.11
> 发布物：GitHub Release wheel（PyPI 未启用）
> 仓库：[Hug7/yun](https://github.com/Hug7/yun)（C++ 求解器）、[Hug7/yunpyopt](https://github.com/Hug7/yunpyopt)（Python 包）
> 相关：[yun SDK 依赖](yun-sdk-dependency.md)、[发布手册](../release.md)

---

## 1. 概览

`yunpyopt` 是 `yun` 求解器的 Python 封装，由两部分组成：

- **领域模型**：纯 Python，`pandas` 读取场景 CSV，覆盖位置、车辆、承运商、订单、距离矩阵等表；
- **`yunpyopt._core`**：pybind11 扩展，进程内调用 `yun`，对外暴露 `Solver` 与 `RESULT_KEYS`。

wheel 内含扩展，安装即用；源码树由 PEP 517 build hook 从 `yun` 的预编译 SDK 构建扩展，不需要 `yun` 源码，也不需要 Conan。

发布物只有 wheel（不发 sdist），文件名形如：

```text
yunpyopt-<version>-cp311-cp311-macosx_14_0_arm64.whl
```

---

## 2. 仓库结构

```text
yunpyopt/
├── .github/workflows/
│   ├── ci.yml                    # PR / main：质量门禁 + 构建测试
│   └── release.yml               # tag v* / 手动：构建并发布 wheel
├── docs/
│   ├── design/                   # 设计与依赖方案
│   └── release.md                # 发布手册
├── scripts/
│   ├── build_ext.py              # PEP 517 build hook，构建 _core
│   ├── fetch_sdk.py              # 获取并校验 yun 预编译 SDK
│   ├── fix_wheel_tag.py          # 按扩展 minos 重写 wheel 平台标签
│   └── convert_sintef_vrptw.py   # 生成 SINTEF 夹具
├── src/yunpyopt/
│   ├── __init__.py               # 领域模型导出 + solver 懒加载
│   ├── solver.py                 # solve() / Solver 封装
│   ├── domain/schema/            # CSV 表模型
│   ├── domain/schema_model.py    # SchemaModel 基类
│   └── _core*.so                 # 构建产物，不提交
├── tests/
│   ├── data/c1_2_1/              # 求解夹具（CSV + Parameter.yaml + Strategy.lua）
│   └── test_*.py
├── pyproject.toml
├── poetry.lock
├── yun-sdk-version.txt           # 固定 yun SDK 版本（当前 0.1.0）
└── README.md
```

---

## 3. 依赖与版本固定

| 依赖 | 来源 | 版本 |
| --- | --- | --- |
| `yun` 求解器 | GitHub Release 的预编译 SDK | `yun-sdk-version.txt` |
| `pybind11` | PEP 517 `build-system.requires` | `>=2.13,<4` |
| `poetry-core` | PEP 517 `build-system.requires` | `>=2.5,<3` |
| `cmake` | 宿主机（CI runner 预装） | `>=3.15` |
| `pandas` | 运行时 | `^3.0.3` |
| `typing-extensions` | 运行时 | `>=4.6` |

SDK 的获取优先级：

1. `YUN_SDK_DIR`：已解压的本地 SDK（开发 / 离线 / CI 预置）；
2. `YUN_SDK_CACHE`（默认 `~/.cache/yunpyopt/sdk/<version>`）中的缓存；
3. 从 `https://github.com/Hug7/yun/releases/download/v<version>/` 下载并校验 `SHA256SUMS`。

覆盖项：`YUN_SDK_VERSION`（版本）、`YUN_SDK_URL` / `YUN_SDK_SHA256`（调试与镜像）。SDK 的产出与版本规则见 [yun SDK 依赖](yun-sdk-dependency.md)。

---

## 4. 构建链路

### 4.1 扩展构建（`scripts/build_ext.py`）

1. `ensure_sdk()` 取得 SDK（缺失时给出可操作的错误提示）；
2. CMake 配置 `build/yun-sdk-binding`：

   | 参数 | 值 |
   | --- | --- |
   | `Python3_EXECUTABLE` | 当前解释器 |
   | `pybind11_DIR` | `python -m pybind11 --cmakedir` |
   | `CMAKE_OSX_DEPLOYMENT_TARGET` | `MACOSX_DEPLOYMENT_TARGET` 或 `14.0` |
   | `CMAKE_OSX_ARCHITECTURES` | `arm64` |
   | `CMAKE_BUILD_TYPE` | `Release` |
   | `CMAKE_SKIP_RPATH` | `ON` |

3. 构建 target `yun_python_binding`；
4. 断言构建目录恰好一个 `_core*.so`，清理 `src/yunpyopt/` 下的旧扩展并复制新产物；
5. 直接导入产物，打印 `RESULT_KEYS` 做冒烟验证。

### 4.2 SDK 内容

SDK 由 `yun` 仓库产出，包含：消费方入口 `CMakeLists.txt`、`include/`（yun 各组件 + fmt/spdlog/yaml-cpp/magic_enum/libfork）、单体静态库 `lib/libyun_sdk.a`、binding 源码 `src/yun_solver_binding.cpp`。`pybind11` 不随 SDK 分发。

### 4.3 wheel 平台标签

`poetry-core` 用构建解释器的 `sys_tags` 生成标签（例如 `macosx_11_0_arm64`），而扩展的实际 minos 更高。`scripts/fix_wheel_tag.py` 在 wheel 构建后：

1. 从 `_core*.so` 读取 `LC_BUILD_VERSION/minos` 与 `lipo` 架构；
2. 把 minos 向上取整到下一个 major（`13.3` → `14_0`），因为 pip 的 macOS 兼容标签只按 `major.0` 枚举；
3. 调用 `wheel tags --remove --python-tag ... --abi-tag ... --platform-tag ...` 重写文件名、`WHEEL` 与 `RECORD`；
4. 已带目标标签时跳过，可重复执行。

结果标签：`cp311-cp311-macosx_14_0_arm64`。

### 4.4 产物校验

- wheel 名含 `-cp311-cp311-macosx_14_0_arm64.whl`；
- `zipfile` 中恰好一个 `.so`，且文件名以 `yunpyopt/_core.` 开头；
- `twine check dist/*` 通过；
- `otool -L` 只列 `/usr/lib/` 或 `/System/Library/`；
- `otool -l` 中无 `LC_RPATH`。

### 4.5 `_core*.so` 的版本控制约定

`src/yunpyopt/_core*.so` 是构建产物，**不提交**；也**不写进 `.gitignore`**——`poetry-core` 会跳过 VCS ignored 文件，导致 wheel 缺失扩展。CI 的 quality job 会检查该文件未被提交。

---

## 5. Python API

### 5.1 包导出与懒加载

`yunpyopt/__init__.py` 直接导出领域模型；`Solver`、`YunSolverError`、`DEFAULT_LOG_LEVEL`、`RESULT_KEYS`、`solve` 通过模块级 `__getattr__` 懒加载，只用领域模型时不会加载二进制扩展。

### 5.2 `solve()`

```python
solve(case_dir, log_dir=None, log_level="info") -> dict[str, str | None]
```

- `case_dir`：接受 `str` 或 `os.PathLike`；需包含场景 CSV 与 `Strategy.lua`，且可写（求解会在其下创建 `output/<request_id>/`）；
- `log_dir`：额外日志目录；不传则该参数关闭，日志仍写入产物目录；
- `log_level`：无法识别时 C++ 侧退化为 `info`；
- 返回值：`loads` / `locations` / `unassigned` / `infeasible` 四个 key，值为绝对路径，未产出为 `None`；
- `loads is None` 不一定是失败：precheck 拦截不可解订单时 `infeasible` 有值而 `loads` 为 `None`；
- 异常：构造或求解失败、`Strategy.lua` 缺失均抛 `YunSolverError`，原始 C++ 消息保留在异常文本中，原异常挂在 `__cause__`；
- 返回 key 会与 `_core` 的 `RESULT_KEYS` 校验，不匹配时提示版本不一致。

行为说明：ALNS 阶段不把最优解写回 workspace，导出的车次是 KNN 构造解，因此 `Strategy.lua` 的 `max_iter` 不影响输出；`solve()` 求解期间释放 GIL，可重复调用。

### 5.3 领域模型

`src/yunpyopt/domain/schema/` 下的模型继承 `SchemaModel`，按表名读取 CSV，覆盖：

- `base_dict`：`Dimension`、`Label`、`LabelApply`、`LabelValue`、`LabelApplyItem`
- `location`：`Location`、`LocationAvailableVehicle`、`LocationLabelValue`、`WorkCalendarDaily`、`WorkCalendarWeekly`、`WorkEffect`、`WorkFixed`
- `vehicle_model`：`VehicleModel`、`VehicleModelDimensionValue`、`VehicleModelLabelValue`
- `carrier`：`Carrier`、`CarrierLabelValue`、`Vehicle`
- `network`：`DistMatrixCode`、`DistMatrix`
- `order`：`CargoOrder`、`CargoSubOrder`、`CargoSubOrderDimensionValue`、`CargoSubOrderLabelValue`

---

## 6. 测试

| 文件 | 内容 |
| --- | --- |
| `tests/test_solver.py` | `_core` 存在性、四 key 契约、重复求解、缺 `Strategy.lua`、`RESULT_KEYS` 一致性 |
| `tests/test_sintef_c1_2_1.py` | 夹具结构不变量 + 真实求解（200 单全部分配） |
| `tests/test_*.py`（领域模型） | 各 CSV 模型的解析与 `__repr__` |

夹具 `tests/data/c1_2_1/`：

- 由 SINTEF Homberger `C1_2_1` 转换生成（`scripts/convert_sintef_vrptw.py`），201 个位置、200 张订单、60 辆车、总需求 3530；
- 表结构与线上场景一致，求解测试会复制到 `tmp_path`，避免在仓库内产生 `output/`。

`pyproject.toml` 中 `testpaths = ["tests"]`、`pythonpath = ["src"]`。缺 `_core` 时 `test_solver.py` 整模块跳过；CI 设置 `YUNPYOPT_REQUIRE_CORE=1`，缺扩展直接失败。

本地校验：

```bash
poetry run ruff check src tests scripts
poetry run ruff format --check src tests scripts
poetry run mypy src
YUNPYOPT_REQUIRE_CORE=1 poetry run pytest -v
```

---

## 7. CI / Release

### 7.1 `ci.yml`（push/PR 到 `main`）

| job | runner | 内容 |
| --- | --- | --- |
| Lint & typecheck（20 min） | `macos-15` | 检查 `_core*.so` 未提交、安装 Poetry 2.5.1、`poetry install --no-root`、ruff check/format、mypy、`poetry check --lock` |
| Build & test wheel（45 min） | `macos-15` | 缓存 SDK、`poetry install`（触发扩展构建）、`YUNPYOPT_REQUIRE_CORE=1 pytest -v`、`poetry build -f wheel`、`fix_wheel_tag.py`、wheel 校验与 `twine check`、干净 venv 冒烟求解、`otool` 依赖/RPATH 检查、上传 `wheel` artifact |

环境：`MACOSX_DEPLOYMENT_TARGET=14.0`；test job 设 `POETRY_VIRTUALENVS_CREATE=false`，让扩展构建落在 runner 的 3.11 解释器上。

### 7.2 `release.yml`（tag `v*` 或手动触发）

- **Build wheel**：校验 tag 与 `pyproject.toml` 版本一致（仅 tag 触发）→ 缓存 SDK → `python -m build --wheel` → `fix_wheel_tag.py` → `twine check` 与 wheel 内容校验 → 干净 venv 冒烟求解 → `otool` 检查 → 上传 artifact；
- **Create GitHub Release**：仅 tag 触发，`needs: build`，用 `softprops/action-gh-release` 上传 `dist/*.whl` 并生成 release notes。

### 7.3 缓存与权限

- SDK 缓存：`~/.cache/yunpyopt/sdk`，key 为 `yun-sdk-${{ hashFiles('yun-sdk-version.txt') }}`；
- 默认权限 `contents: read`；仅 release job 提升为 `contents: write`。

---

## 8. 发布流程

1. 更新 `pyproject.toml` 版本与 `CHANGELOG.md`；
2. 确认 `yun-sdk-version.txt` 指向已发布的 `yun` SDK；
3. 打 tag `v<version>` 并 push，触发 `release.yml`；
4. 在 GitHub Release 下载 wheel，按 [发布手册](../release.md) 做安装与求解验证。

---

## 9. 约束

- **平台**：仅 macOS 14.0+ arm64、CPython 3.11；不支持 Linux / Windows / Intel Mac / 3.12+。
- **最低系统 14.0**：C++ 使用 `std::format` 与浮点 `std::to_chars`，需要 macOS 13.3+；pip 的 macOS 兼容标签按 `major.0` 枚举，故 wheel 标签取 `macosx_14_0_arm64`。
- **工具链**：使用 `macos-15` runner（Xcode 16+）。用 pyenv 在 macOS 26 上构建的 3.11 会输出 `macosx-26.3-arm64` 标签，不能用于发布；发布构建以 CI 为准。
- **ABI**：SDK 为 macOS arm64 + C++20 + 部署目标 14.0，消费方必须匹配。
- **SDK 不可变**：同一 SDK 版本不覆盖发布，否则 `SHA256SUMS` 变化影响复现。
- **求解行为**：导出的车次是 KNN 构造解（见 §5.2）。
