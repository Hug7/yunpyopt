# yun SDK 依赖

> 平台：macOS arm64 / Linux x86_64 / Linux arm64 / Windows x86_64；CPython 3.11
> 关联：[总体封装与发布方案](yunpyopt-packaging-and-release-design.md)
> 上游文档：[yun SDK 使用手册](https://github.com/Hug7/yun/blob/main/docs/sdk_guide.md)

---

## 1. 概览

`yunpyopt` 不引入 `yun` 源码，只消费 `yun` GitHub Release 提供的**预编译 SDK**。
SDK 内含 headers、单体静态库、binding 源码与 CMake 入口；`yunpyopt` 只编译 pybind11
binding，`pybind11` 由 `yunpyopt` 的 `build-system.requires` 提供。

```text
yun (源码 + Conan)  --scripts/build_sdk.py-->  yun-sdk-<v>-<platform>.tar.gz
                                                        |
                                                        v
yunpyopt (CMake + pybind11) --scripts/build_ext.py--> yunpyopt/_core*.so|.pyd --> wheel
```

---

## 2. 平台矩阵

| 平台 | 资产 | 编译器/运行时 | 库文件 | wheel 标签 |
| --- | --- | --- | --- | --- |
| macOS arm64 | `yun-sdk-0.2.0-macos-arm64.tar.gz` | AppleClang 16+，macOS 14.0+ | `lib/libyun_sdk.a` | `macosx_14_0_arm64` |
| Linux x86_64 | `yun-sdk-0.2.0-linux-x86_64.tar.gz` | GCC 14，glibc ≥ 2.28 | `lib/libyun_sdk.a` | `manylinux_2_28_x86_64` |
| Linux arm64 | `yun-sdk-0.2.0-linux-arm64.tar.gz` | GCC 14，glibc ≥ 2.28 | `lib/libyun_sdk.a` | `manylinux_2_28_aarch64` |
| Windows x86_64 | `yun-sdk-0.2.0-windows-x86_64.tar.gz` | clang-cl 17+ + MSVC STL，`/MD` | `lib/yun_sdk.lib` | `win_amd64` |

SDK 版本由 [`yun-sdk-version.txt`](../../yun-sdk-version.txt) 固定，当前为 `0.2.0`。
Release 附带合并的 `SHA256SUMS`；同一版本不覆盖发布。

不在支持范围：macOS Intel、Windows arm64、musl Linux、MSVC `cl.exe`、MinGW。

---

## 3. SDK 内容

```text
yun-sdk-<version>-<platform>/
├── CMakeLists.txt                  # 消费方构建 _core 的入口
├── VERSION
├── SDK_PLATFORM
├── LICENSE
├── include/
│   ├── yun/{common,scenario,problem,algorithm,solver}/
│   ├── fmt/ spdlog/ yaml-cpp/ magic_enum/ sol/ libfork/ lua.hpp ...
├── lib/
│   ├── libyun_sdk.a                # Windows: yun_sdk.lib
│   └── cmake/yun/yunConfig.cmake
│       cmake/yun/yunConfigVersion.cmake
└── src/yun_solver_binding.cpp
```

`libyun_sdk.a` / `yun_sdk.lib` 已合并 `yun_solver`、`yun_algorithm`、`yun_problem`、
`yun_scenario` 与 fmt/spdlog/yaml-cpp/lua 的静态库；`libfork`、`sol2`、`magic_enum`
是 header-only。生成的 `_core` 只依赖系统库（Windows 另依赖 MSVC 运行库）。

SDK 的 `CMakeLists.txt`：

```cmake
find_package(yun CONFIG REQUIRED HINTS "${CMAKE_CURRENT_SOURCE_DIR}")
find_package(Python3 REQUIRED COMPONENTS Interpreter Development.Module)
find_package(pybind11 CONFIG REQUIRED)

pybind11_add_module(yun_python_binding WITH_SOABI src/yun_solver_binding.cpp)
target_link_libraries(yun_python_binding PRIVATE yun::sdk)
set_target_properties(yun_python_binding PROPERTIES OUTPUT_NAME "_core")
```

`yunConfig.cmake` 导出 `yun::sdk`，携带 include 目录、`cxx_std_20`、
`SPDLOG_COMPILED_LIB;SPDLOG_FMT_EXTERNAL;YAML_CPP_STATIC_DEFINE` 与平台系统库
（Linux `Threads::Threads;dl;m`，macOS `Threads::Threads`，Windows 无）。

---

## 4. 获取 SDK（`scripts/fetch_sdk.py`）

优先级：

1. `YUN_SDK_DIR`：本地已解压 SDK（需存在 `lib/<platform lib>`）；
2. `YUN_SDK_CACHE`（默认 `~/.cache/yunpyopt/sdk/<version>/<tag>`）；
3. 从 `https://github.com/Hug7/yun/releases/download/v<version>/` 下载。

下载后用 Release 的 `SHA256SUMS` 校验；解压到暂存目录，校验通过后再整体改名，避免半成品
缓存。可覆盖项：

| 变量 | 作用 |
| --- | --- |
| `YUN_SDK_VERSION` | 覆盖 `yun-sdk-version.txt` |
| `YUN_SDK_DIR` | 使用本地 SDK，跳过下载 |
| `YUN_SDK_CACHE` | 缓存根目录 |
| `YUN_SDK_URL` | 覆盖 tarball 地址（测试/镜像） |
| `YUN_SDK_SHA256` | 直接指定 tarball 校验值 |
| `YUN_SDK_SHA256SUMS_URL` | 覆盖 `SHA256SUMS` 地址 |

平台识别统一在 `scripts/sdk_platform.py`，`fetch_sdk.py`、`build_ext.py`、
`fix_wheel_tag.py` 共用，避免三处漂移。

---

## 5. 构建扩展（`scripts/build_ext.py`）

1. `detect_platform()` 得到 `SdkPlatform`；
2. `_check_toolchain()`：CMake ≥ 3.24；Linux 检查 GCC ≥ 13.2；Windows 检查
   `clang-cl` + `ninja`；
3. `ensure_sdk(spec=...)` 取得 SDK；
4. CMake 配置 `build/yun-sdk-binding`：

   | 平台 | 关键参数 |
   | --- | --- |
   | macOS | `CMAKE_OSX_DEPLOYMENT_TARGET=14.0`、`CMAKE_OSX_ARCHITECTURES=arm64` |
   | Linux | `CMAKE_POSITION_INDEPENDENT_CODE=ON`、`CMAKE_CXX_COMPILER=$CXX`、`-static-libstdc++ -static-libgcc` |
   | Windows | `-G Ninja`、`CMAKE_CXX_COMPILER=clang-cl`、`CMAKE_MSVC_RUNTIME_LIBRARY=MultiThreadedDLL` |

5. 构建 target `yun_python_binding`；
6. 断言构建目录恰好一个 `_core*<suffix>`，清理 `src/yunpyopt/` 下旧扩展并复制；
7. 生成 `src/yunpyopt/_build_info.py`（`SDK_VERSION` / `SDK_PLATFORM`）；
8. 冒烟导入，打印 `RESULT_KEYS`。

扩展文件：

| 平台 | 文件名示例 |
| --- | --- |
| macOS | `_core.cpython-311-darwin.so` |
| Linux | `_core.cpython-311-x86_64-linux-gnu.so` |
| Windows | `_core.cp311-win_amd64.pyd` |

`src/yunpyopt/_core*` 与 `_build_info.py` 是构建产物：不提交，也不写进 `.gitignore`
（poetry-core 会跳过 VCS ignored 文件，导致 wheel 缺失扩展）。

---

## 6. 约束

- **ABI 匹配**：SDK 是同一编译器家族的静态库；Linux GCC、macOS AppleClang、Windows
  clang-cl，不做跨编译器 ABI 承诺。升级 SDK 版本必须重新构建扩展。
- **Linux 基线**：manylinux_2_28（glibc ≥ 2.28）；扩展静态链接 `libstdc++`/`libgcc`，
  避免要求 GCC 14 运行库。
- **Windows 运行时**：SDK 以 `/MD` 构建，消费端必须同样 `/MD`；wheel 不打包
  `MSVCP140.dll` / `VCRUNTIME140.dll`，用户需安装 VC++ 2015-2022 x64 运行库。
- **Windows 路径**：SDK 的 C++ 侧仍使用窄路径（`std::string` + `std::ifstream`），
  非 ASCII 案例路径会打开失败；`yunpyopt` 在 Windows 上会提前抛出 `ValueError`。
- **macOS 最低版本**：SDK 部署目标 14.0；wheel tag 取 `macosx_14_0_arm64`。
- **SDK 不可变**：同一版本不覆盖发布，否则 `SHA256SUMS` 变化影响复现。

---

## 7. 发布顺序（硬约束）

1. `yun` 发布 `v<version>` SDK Release（四个 tarball + `SHA256SUMS`）；
2. `yunpyopt` 更新 `yun-sdk-version.txt` 并 push；
3. `yunpyopt` 打 `v<version>` tag，触发四平台 wheel 构建与 Release。

SDK 不存在时 `fetch_sdk.py` 报错并提示先运行 `yun` 的 SDK Release workflow。
