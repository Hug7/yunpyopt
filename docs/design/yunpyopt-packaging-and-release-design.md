# yunpyopt 封装与发布

> 平台：macOS arm64、Linux x86_64、Linux arm64、Windows x86_64；CPython 3.11
> 发布物：GitHub Release wheel（PyPI 暂未启用）
> 仓库：[Hug7/yun](https://github.com/Hug7/yun)（C++ 求解器）、[Hug7/yunpyopt](https://github.com/Hug7/yunpyopt)（Python 包）
> 相关：[yun SDK 依赖](yun-sdk-dependency.md)、[发布手册](../release.md)

---

## 1. 概览

`yunpyopt` 是 `yun` 求解器的 Python 封装，由两部分组成：

- **领域模型**：纯 Python，`pandas` 读写场景 CSV，覆盖位置、车辆、承运商、订单、距离矩阵等表；
- **`yunpyopt._core`**：pybind11 扩展，进程内调用 `yun`，对外暴露 `Solver` 与 `RESULT_KEYS`。

wheel 内含扩展，安装即用；源码树由 PEP 517 build hook 从 `yun` 预编译 SDK 构建，不需要
`yun` 源码或 Conan。发布物只有 wheel（不发 sdist）。

支持矩阵：

| 平台 | 架构 | 最低运行时 | wheel 标签 |
| --- | --- | --- | --- |
| macOS | arm64 | macOS 14.0+ | `macosx_14_0_arm64` |
| Linux | x86_64 | glibc ≥ 2.28 | `manylinux_2_28_x86_64` |
| Linux | arm64 | glibc ≥ 2.28 | `manylinux_2_28_aarch64` |
| Windows | x86_64 | Windows 10/11 x64 + VC++ 2015-2022 运行库 | `win_amd64` |

---

## 2. 仓库结构

```text
yunpyopt/
├── .github/
│   ├── actions/
│   │   ├── setup-poetry/action.yml
│   │   └── build-wheel/action.yml      # 跨平台：构建、修标签、校验、冒烟、动态依赖
│   └── workflows/
│       ├── ci.yml                      # quality + macos/linux/windows 矩阵
│       └── release.yml                 # tag v* / 手动：四平台构建 + 聚合 Release
├── docs/
│   ├── design/
│   └── release.md
├── scripts/
│   ├── sdk_platform.py                 # 平台事实的唯一来源
│   ├── build_ext.py                    # PEP 517 build hook
│   ├── fetch_sdk.py                    # 四平台 SDK 下载/校验/缓存
│   ├── fix_wheel_tag.py                # macOS 修 minos；Linux auditwheel；Windows 校验
│   └── convert_sintef_vrptw.py         # 生成 SINTEF 夹具
├── src/yunpyopt/
│   ├── __init__.py                     # 领域模型导出 + solver 懒加载
│   ├── solver.py                       # solve() / Solver / SolveResult
│   ├── _build_info.py                  # 构建时生成，不提交
│   ├── domain/schema/                  # CSV 表模型
│   ├── domain/schema_model.py
│   └── _core*.so|.pyd                  # 构建产物，不提交
├── tests/
│   ├── data/c1_2_1/
│   ├── test_solver.py
│   ├── test_solver_api.py
│   ├── test_sdk_platform.py
│   ├── test_fetch_sdk.py
│   ├── test_build_ext.py
│   ├── test_wheel_tag.py
│   └── test_*.py（领域模型）
├── pyproject.toml
├── poetry.lock
├── yun-sdk-version.txt                 # 当前 0.2.0
└── README.md
```

---

## 3. 依赖与版本固定

| 依赖 | 来源 | 版本 |
| --- | --- | --- |
| `yun` 求解器 | GitHub Release 预编译 SDK | `yun-sdk-version.txt`（0.2.0） |
| `pybind11` | PEP 517 `build-system.requires` | `>=2.13,<4` |
| `poetry-core` | PEP 517 `build-system.requires` | `>=2.5,<3` |
| `cmake` | 宿主机 / CI | `>=3.24` |
| `pandas` | 运行时 | `^3.0.3` |
| `typing-extensions` | 运行时 | `>=4.6` |

SDK 获取优先级、覆盖变量与校验见 [yun SDK 依赖](yun-sdk-dependency.md)。

---

## 4. 构建链路

### 4.1 扩展构建（`scripts/build_ext.py`）

1. `detect_platform()` 返回 `SdkPlatform`；
2. `_check_toolchain()`：CMake；Linux GCC ≥ 13.2；Windows clang-cl + Ninja；
3. `ensure_sdk(spec=...)`；
4. CMake 配置 `build/yun-sdk-binding`：
   - macOS：`CMAKE_OSX_DEPLOYMENT_TARGET=14.0`、`CMAKE_OSX_ARCHITECTURES=arm64`；
   - Linux：PIC、`CMAKE_CXX_COMPILER=$CXX`、`-static-libstdc++ -static-libgcc`；
   - Windows：`-G Ninja`、`clang-cl`、`CMAKE_MSVC_RUNTIME_LIBRARY=MultiThreadedDLL`；
5. 构建 target `yun_python_binding`；
6. 断言恰好一个 `_core*<suffix>`，清理旧扩展并复制到 `src/yunpyopt/`；
7. 生成 `_build_info.py`；
8. 冒烟导入并打印 `RESULT_KEYS`。

### 4.2 wheel 平台标签

| 平台 | 处理 | 结果 |
| --- | --- | --- |
| macOS | `otool` 读 `LC_BUILD_VERSION/minos` + `lipo` 架构；`wheel tags` 重写 | `macosx_14_0_arm64` |
| Linux | `auditwheel repair --plat manylinux_2_28_<arch> --only-plat`，删除未修输入 | `manylinux_2_28_<arch>` |
| Windows | 校验 `cp311-cp311-win_amd64` 与唯一 `_core*.pyd` | `win_amd64` |

macOS 的 minos 向上取整到下一个 major（13.3 → 14_0），因为 pip 的 macOS 兼容标签只按
`major.0` 枚举。

### 4.3 产物校验

- wheel 名与平台标签匹配；
- 恰好一个扩展，路径以 `yunpyopt/_core.` 开头；
- `twine check` 通过；
- macOS：`otool -L` 只列系统库，且无 `LC_RPATH`；
- Linux：`auditwheel show` 显示 `manylinux_2_28`，不依赖外部 `libstdc++`，无 RPATH/RUNPATH；
- Windows：`dumpbin /dependents` 只包含约定系统/运行库 DLL；
- clean venv 安装并真实求解 `tests/data/c1_2_1`。

### 4.4 构建产物的版本控制约定

`src/yunpyopt/_core*.so|.pyd` 与 `_build_info.py` 是构建产物，**不提交**；也**不写进
`.gitignore`**——poetry-core 会跳过 VCS ignored 文件，导致 wheel 缺失扩展。CI 的 quality
job 会检查它们未被提交。

---

## 5. Python API

### 5.1 包导出与懒加载

`yunpyopt/__init__.py` 直接导出领域模型；`Solver`、`SolveResult`、`YunSolverError`、
`DEFAULT_LOG_LEVEL`、`RESULT_KEYS`、`SDK_VERSION`、`SDK_PLATFORM`、`solve` 通过模块级
`__getattr__` 懒加载，只用领域模型时不会加载二进制扩展。

### 5.2 `solve()`

```python
solve(case_dir, log_dir=None, log_level="info") -> SolveResult
```

- `case_dir` 接受 `str` / `os.PathLike`；需包含场景 CSV、`Parameter.yaml`、`Strategy.lua`，且可写；
- `log_dir` 可选；`log_level` 无法识别时 C++ 侧退化为 `info`；
- 返回 5 个 key：`plan_summary`、`loads`、`locations`、`unassigned`、`infeasible`，
  值为绝对路径，未产出为 `None`；
- `loads is None` 可能只是 precheck 拦截：此时 `infeasible` 有值；
- 异常统一为 `YunSolverError`，原始 C++ 消息保留，原异常在 `__cause__`；
- 返回 key 与 `_core.RESULT_KEYS` 校验，不一致提示版本不匹配；
- 求解期间释放 GIL；每次调用新建 `Solver`，因此使用新的 `request_id`。

### 5.3 `Solver`

- `Solver(case_dir, log_dir=None, log_level="info")`；
- `solve()`：重复调用复用同一 `request_id`/输出目录，后一次覆盖前一次；
- `output_dir`、`case_dir`、`log_level`；
- `close()` 与 context manager；关闭后再调用抛 `YunSolverError`。

### 5.4 构建信息

`SDK_VERSION` / `SDK_PLATFORM` 由 `scripts/build_ext.py` 写入 `_build_info.py`，用于定位
wheel 构建所用的 SDK 版本与平台；源码树未构建时为 `"unknown"`。

---

## 6. 测试

| 文件 | 内容 |
| --- | --- |
| `tests/test_solver.py` | 5 个结果 key、`plan_summary`、重复调用、缺 `Strategy.lua`、非 ASCII 路径 |
| `tests/test_solver_api.py` | `Solver` 复用/context manager、`SDK_VERSION`、`plan_summary` |
| `tests/test_sdk_platform.py` | 四平台映射与不支持平台 |
| `tests/test_fetch_sdk.py` | SDK 命名/URL/本地目录/平台库文件 |
| `tests/test_build_ext.py` | macOS/Linux/Windows CMake 参数 |
| `tests/test_wheel_tag.py` | macOS minos 取整、Python/ABI tag 解析 |
| `tests/test_*.py`（领域模型） | 各 CSV 模型的解析与 `__repr__` |

夹具 `tests/data/c1_2_1/` 由 SINTEF Homberger `C1_2_1` 转换生成：201 个位置、200 张订单、
60 辆车、总需求 3530；求解测试复制到 `tmp_path`，避免在仓库内产生 `output/`。

CI 设置 `YUNPYOPT_REQUIRE_CORE=1`，缺扩展直接失败，避免“全 skip 也算绿”。

---

## 7. CI / Release

### 7.1 `ci.yml`

| job | runner | 内容 |
| --- | --- | --- |
| `quality` | `ubuntu-24.04` | `_core*`/`_build_info.py` 未提交；ruff、mypy、`poetry check --lock` |
| `test-macos` | `macos-15` | 构建/校验 wheel → clean venv 安装 → pytest |
| `test-linux` | `ubuntu-24.04` / `ubuntu-24.04-arm` + manylinux_2_28 容器 | 同上 |
| `test-windows` | `windows-2022` | clang-cl + Ninja + MSVC 环境；同上 |

复合 action `.github/actions/build-wheel` 负责：SDK 缓存（Linux 跳过）、`python -m build`、
修标签、内容校验、clean venv 冒烟、动态依赖检查、上传 artifact。

### 7.2 `release.yml`

- `version` job：校验 tag 与 `pyproject.toml` 版本、`yun-sdk-version.txt`；
- `build-macos` / `build-linux`（x86_64/arm64 matrix）/ `build-windows`：构建并上传 artifact；
- `release` job：下载 `wheel-*`，校验四个 wheel，生成 `SHA256SUMS`，创建 GitHub Release；
- `workflow_dispatch` 只构建 artifact，不创建 Release；
- `release` environment 可配人工审批。

### 7.3 缓存与权限

- SDK 缓存 key：`yun-sdk-<hash>-<runner.os>-<runner.arch>`；Linux 在容器内不做缓存；
- 默认权限 `contents: read`；仅 release job 提升为 `contents: write`。

---

## 8. 发布流程

1. 更新 `pyproject.toml` 版本与 `CHANGELOG.md`；
2. 确认 `yun-sdk-version.txt` 指向已发布 SDK；
3. 打 tag `v<version>` 并 push，触发 `release.yml`；
4. 从 GitHub Release 下载四个 wheel，按 [发布手册](../release.md) 验证。

---

## 9. 约束

- **平台**：macOS arm64、Linux x86_64/arm64、Windows x86_64；不支持 macOS Intel、
  Windows arm64、musl Linux、Python 3.12+。
- **Linux**：manylinux_2_28 基线；静态链接 `libstdc++`/`libgcc`。
- **Windows**：clang-cl + `/MD`；用户需 VC++ 2015-2022 x64 运行库。
- **macOS**：部署目标 14.0；wheel tag `macosx_14_0_arm64`。
- **ABI**：SDK 同编译器家族；升级 SDK 必须重建扩展。
- **SDK 不可变**：同一版本不覆盖发布。
- **Windows 非 ASCII 路径**：仍在验证；失败时先使用纯英文案例目录。
