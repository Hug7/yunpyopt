# yunpyopt

[`yun`](https://github.com/Hug7/yun) VRP/ALNS 求解器的 Python 调用层。

`yunpyopt` 包含纯 Python 领域模型，以及用于进程内求解的 pybind11 扩展
`yunpyopt._core`。目前支持四个平台：

| 平台 | 架构 | 最低运行时 | wheel 标签 |
| --- | --- | --- | --- |
| macOS | arm64 | macOS 14.0+ | `macosx_14_0_arm64` |
| Linux | x86_64 | glibc ≥ 2.28（manylinux_2_28） | `manylinux_2_28_x86_64` |
| Linux | arm64 | glibc ≥ 2.28（manylinux_2_28） | `manylinux_2_28_aarch64` |
| Windows | x86_64 | Windows 10/11 x64 + VC++ 2015-2022 运行库 | `win_amd64` |

当前只发布 CPython 3.11。macOS Intel、Windows arm64、musl Linux（Alpine）暂不支持。

## 安装

0.2.0 通过 GitHub Release 分发（PyPI 尚未启用），按平台选择对应 wheel：

```bash
# macOS arm64
pip install https://github.com/Hug7/yunpyopt/releases/download/v0.2.0/yunpyopt-0.2.0-cp311-cp311-macosx_14_0_arm64.whl

# Linux x86_64
pip install https://github.com/Hug7/yunpyopt/releases/download/v0.2.0/yunpyopt-0.2.0-cp311-cp311-manylinux_2_28_x86_64.whl

# Linux arm64
pip install https://github.com/Hug7/yunpyopt/releases/download/v0.2.0/yunpyopt-0.2.0-cp311-cp311-manylinux_2_28_aarch64.whl

# Windows x64
pip install https://github.com/Hug7/yunpyopt/releases/download/v0.2.0/yunpyopt-0.2.0-cp311-cp311-win_amd64.whl
```

Windows 需要安装 **Microsoft Visual C++ 2015-2022 Redistributable (x64)**；wheel 不打包
`MSVCP140.dll` / `VCRUNTIME140.dll`。Linux wheel 已静态链接 `libstdc++`/`libgcc`，
不要求系统安装 GCC 14 的运行库。

安装后可以先确认包版本、SDK 版本与目标平台：

```python
import yunpyopt

print(yunpyopt.__version__)      # yunpyopt 包版本
print(yunpyopt.SDK_VERSION)      # 编译 _core 时使用的 yun SDK 版本
print(yunpyopt.SDK_PLATFORM)     # macos-arm64 / linux-x86_64 / linux-arm64 / windows-x86_64
```

## 用法

### 一行求解

```python
from pathlib import Path

from yunpyopt import solve

result = solve("path/to/c1_2_1", log_level="info")
# {
#     "plan_summary": ".../PlanSummary.json",
#     "loads": ".../Loads.json",
#     "locations": ".../LoadLocations.json",
#     "unassigned": ".../UnassignedCargoOrders.json",
#     "infeasible": None,
# }

if result["loads"] is None:
    # precheck 阻止了求解；查看 infeasible 了解不可解订单
    print("blocked:", result["infeasible"])
else:
    print(Path(result["loads"]))
```

`solve()` 接受 `str` 或 `os.PathLike`，求解期间释放 GIL，可重复调用。每次调用都会创建新的
`Solver`，因此使用新的 `request_id` 和新的输出目录。

### 显式使用 `Solver`

需要读取输出目录、复用同一个求解上下文时，可以直接使用 `Solver`：

```python
from pathlib import Path

from yunpyopt import Solver

with Solver("path/to/c1_2_1", log_dir="path/to/logs", log_level="info") as solver:
    result = solver.solve()
    print(solver.output_dir)   # <case_dir>/output/<request_id>
    print(solver.case_dir)     # 归一化后的案例绝对路径
    print(solver.log_level)

assert result["loads"] is not None
loads = Path(result["loads"])
```

同一个 `Solver` 实例重复调用 `solve()` 会复用同一个 `request_id` 和输出目录，后一次会覆盖
前一次的产物；如果需要新的 `request_id`，请新建 `Solver` 或调用模块级 `solve()`。

`solve()` / `Solver.solve()` 的返回值是 `SolveResult`（`TypedDict`），也可以用于类型标注：

```python
from yunpyopt import SolveResult, solve

result: SolveResult = solve("path/to/c1_2_1")
```

案例目录需要场景 CSV、`Parameter.yaml` 与 `Strategy.lua`，且必须可写（求解会在其下创建
`output/<request_id>/`）。`log_dir` 可选；不传时该参数关闭，日志仍会写到产物目录。

Windows 上案例路径必须是纯 ASCII；否则 `Solver` 会抛出带说明的 `ValueError`，请先把案例
移动到英文路径。

### 结果 key

| key | 文件 | 说明 |
| --- | --- | --- |
| `plan_summary` | `PlanSummary.json` | 规划结果汇总（0.2.0 新增） |
| `loads` | `Loads.json` | 车次与路径 |
| `locations` | `LoadLocations.json` | 位置装载信息 |
| `unassigned` | `UnassignedCargoOrders.json` | 未分配订单 |
| `infeasible` | `InfeasibleCargoOrders.json` | precheck 判定的不可解订单 |

`loads is None` 不一定是失败：precheck 拦截整条链路时，`infeasible` 有值而 `loads` 为
`None`；此时 `plan_summary` 也可能为 `None`。

结果文件都是 JSON，可以直接读取：

```python
import json

loads = json.loads(Path(result["loads"]).read_text(encoding="utf-8"))
```

## 从源码构建

前置条件（所有平台）：

- CPython 3.11
- CMake ≥ 3.24
- Poetry 2.5+
- `yun` 0.2.0 SDK：`scripts/fetch_sdk.py` 会从 GitHub Release 下载并校验；离线/本地开发可用
  `YUN_SDK_DIR` 指向已解压的 SDK

```bash
git clone https://github.com/Hug7/yunpyopt.git
cd yunpyopt
poetry install
YUNPYOPT_REQUIRE_CORE=1 poetry run pytest -v
```

`poetry install` 会执行 PEP 517 build hook `scripts/build_ext.py`：下载 SDK、构建
`yunpyopt._core`，再把产物复制到 `src/yunpyopt/`。SDK 版本固定在
[`yun-sdk-version.txt`](yun-sdk-version.txt)。

### macOS（arm64，14.0+）

需要 Xcode Command Line Tools（AppleClang 16+）：

```bash
poetry install
poetry build -f wheel
poetry run python scripts/fix_wheel_tag.py dist
```

### Linux（x86_64 / arm64）

SDK 以 GCC 14 + manylinux_2_28 为基线；构建环境建议使用
`quay.io/pypa/manylinux_2_28_x86_64` / `..._aarch64` 容器：

```bash
source /opt/rh/gcc-toolset-14/enable
PY=/opt/python/cp311-cp311/bin/python
export PATH="$(dirname "$PY"):$PATH"
export CC="$(command -v gcc)" CXX="$(command -v g++)"

"$PY" -m pip install build twine wheel auditwheel
"$PY" -m build --wheel --outdir dist
"$PY" scripts/fix_wheel_tag.py dist
```

`fix_wheel_tag.py` 会调用 `auditwheel repair --plat manylinux_2_28_* --only-plat`，并校验结果。
`--only-plat` 保证 wheel 只带目标 `manylinux_2_28` 标签，不会出现
`manylinux_2_26.manylinux_2_28` 这类复合标签。

Linux 扩展使用 `-static-libstdc++ -static-libgcc`，避免依赖 GCC 14 的
`libstdc++.so.6`。

### Windows（x64）

需要：

- Visual Studio 2022 Build Tools（C++ 工作负载 + Windows SDK；只用其 MSVC STL、链接器与 SDK）
- LLVM 17+，`clang-cl` 在 `PATH`
- CMake、Ninja、Python 3.11 x64
- 在 VS 开发者环境（或 `ilammy/msvc-dev-cmd` / `TheMrMilchmann/setup-msvc-dev`）中执行

```bat
python -m pip install build twine wheel ninja
python -m build --wheel --outdir dist
python scripts\fix_wheel_tag.py dist
```

Windows 只支持 clang-cl（不支持 MSVC `cl.exe` 或 MinGW），运行时为动态 CRT `/MD`。
构建脚本会把标准输出切到 UTF-8，避免 cp1252 控制台下打印中文失败。

### 本地产物

```bash
# 只重建扩展
python scripts/build_ext.py

# 构建 wheel
poetry build -f wheel
poetry run python scripts/fix_wheel_tag.py dist
```

`src/yunpyopt/_core*.so` / `.pyd` 与 `src/yunpyopt/_build_info.py` 是构建产物：**不要提交**，
也不要写进 `.gitignore`（poetry-core 会跳过 VCS ignored 文件，导致 wheel 缺失扩展）。
注意 `.gitignore` 的 `*.py[codz]` 会匹配 Windows 的 `.pyd`，Windows 扩展需要显式取消忽略。

## 开发

```bash
poetry run ruff check src tests scripts
poetry run ruff format --check src tests scripts
poetry run mypy src
YUNPYOPT_REQUIRE_CORE=1 poetry run pytest -v
```

发布流程见 [docs/release.md](docs/release.md)，SDK 依赖说明见
[docs/design/yun-sdk-dependency.md](docs/design/yun-sdk-dependency.md)。

## 已知限制

- 仅 CPython 3.11；3.12/3.13 尚未提供 wheel。
- 不提供 macOS Intel、Windows arm64、musl Linux 产物。
- Windows 版当前不支持非 ASCII 案例路径：底层 SDK 0.2.0 仍使用窄路径，`Solver` 会抛出带
  说明的 `ValueError`；请把案例目录放到纯英文路径。当前继续固定使用 yun SDK 0.2.0，
  本轮不升级；宽路径支持留待后续版本单独评估。
- `Strategy.lua` 的 `max_iter` 目前不影响导出结果：ALNS 最优解没有写回 workspace，导出的是
  KNN 构造解。

## 许可证

Apache-2.0
