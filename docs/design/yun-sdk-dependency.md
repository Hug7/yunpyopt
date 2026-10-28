# yun SDK 依赖

> 平台：macOS 14.0+（arm64）/ CPython 3.11
> 关联：[总体封装与发布方案](yunpyopt-packaging-and-release-design.md)

---

## 1. 概览

`yunpyopt` 不引入 `yun` 源码，只消费 `yun` GitHub Release 提供的**预编译 SDK**：

- SDK 内含 headers、单体静态库、binding 源码与 CMake 入口；
- `yunpyopt` 用 `yun-sdk-version.txt` 固定 SDK 版本，构建时只编译 pybind11 binding；
- `pybind11` 由 `yunpyopt` 的 `build-system.requires` 提供，SDK 不附带。

```text
yun (源码 + Conan)  --build_sdk.py-->  yun-sdk-<v>-macos-arm64.tar.gz
                                              |
                                              v
yunpyopt (CMake + pybind11)  --build_ext.py-->  yunpyopt/_core*.so  -->  wheel
```

---

## 2. SDK 内容

```text
yun-sdk-<version>-macos-arm64/
├── CMakeLists.txt                  # 消费方构建 _core 的入口
├── VERSION
├── SDK_PLATFORM
├── include/
│   ├── yun/
│   │   ├── common/
│   │   ├── scenario/
│   │   ├── problem/
│   │   ├── algorithm/
│   │   └── solver/
│   ├── fmt/
│   ├── spdlog/
│   ├── yaml-cpp/
│   ├── magic_enum/
│   └── libfork/
├── lib/libyun_sdk.a                # yun_* + spdlog/fmt/yaml-cpp/lua 单体静态库
└── src/yun_solver_binding.cpp
```

- 单体静态库由 `libtool -static` 合并，消费方只链接一个 `.a`；
- 依赖头文件按 binding 编译时的实际 include 路径收集，消费方不需要 Conan；
- 生成的 `_core.so` 只链系统库（`libc++` / `libSystem`），不携带第三方 dylib。

---

## 3. 生产端（yun）

### 3.1 `scripts/build_sdk.py`

1. CMake Release 配置：`YUN_BUILD_PYTHON=ON`、`YUN_BUILD_TESTS=OFF`、`CMAKE_OSX_DEPLOYMENT_TARGET=14.0`；脚本生成 `include(default) + compiler.cppstd=20` 的 Conan host profile。
2. 构建 `yun_python_binding`，取：
   - `compile_commands.json` 中 binding 的 include 路径；
   - `python/CMakeFiles/yun_python_binding.dir/link.txt` 中的完整 `.a` 列表。
3. 复制 yun 五个组件与依赖的头文件。
4. `libtool -static -o lib/libyun_sdk.a` 合并 yun 与第三方静态库。
5. 复制 `python/yun_solver_binding.cpp` 与 `python/sdk/CMakeLists.txt`。
6. 生成 `dist/sdk/yun-sdk-<version>-macos-arm64.tar.gz` 与 `SHA256SUMS`。

### 3.2 SDK 的 `CMakeLists.txt`

```cmake
find_package(Python3 REQUIRED COMPONENTS Interpreter Development.Module)
find_package(pybind11 CONFIG REQUIRED)

add_library(yun_sdk STATIC IMPORTED)
set_target_properties(yun_sdk PROPERTIES
    IMPORTED_LOCATION "${CMAKE_CURRENT_SOURCE_DIR}/lib/libyun_sdk.a")
target_include_directories(yun_sdk INTERFACE ...)

pybind11_add_module(yun_python_binding WITH_SOABI src/yun_solver_binding.cpp)
target_compile_definitions(yun_python_binding PRIVATE
    SPDLOG_COMPILED_LIB SPDLOG_FMT_EXTERNAL YAML_CPP_STATIC_DEFINE)
target_link_libraries(yun_python_binding PRIVATE yun_sdk)
```

### 3.3 `.github/workflows/sdk-release.yml`

- 触发：`v*` tag 或 `workflow_dispatch`（输入 `version`）；
- 校验 tag/输入版本与 `CMakeLists.txt` 的 `project(yun VERSION ...)` 一致；
- `macos-15`（Xcode 16+）+ Python 3.11 + Conan 缓存；
- 上传 `dist/*`（tarball + `SHA256SUMS`）；tag 触发时创建 GitHub Release。

### 3.4 版本规则

SDK 版本 = `project(yun VERSION ...)` = tag `v<version>`（与 yunpyopt 一致）；已发布版本不覆盖，C++ 变更即 bump 版本。

---

## 4. 消费端（yunpyopt）

### 4.1 版本固定

```text
yun-sdk-version.txt   # 当前 0.1.0
```

下载地址：

```text
https://github.com/Hug7/yun/releases/download/v<version>/yun-sdk-<version>-macos-arm64.tar.gz
https://github.com/Hug7/yun/releases/download/v<version>/SHA256SUMS
```

### 4.2 `scripts/fetch_sdk.py`

优先级：

1. `YUN_SDK_DIR`：已解压 SDK（需存在 `lib/libyun_sdk.a`）；
2. `YUN_SDK_CACHE`（默认 `~/.cache/yunpyopt/sdk/<version>`）缓存；
3. 下载 → 校验 `SHA256SUMS` → 解压。

覆盖项：`YUN_SDK_VERSION`、`YUN_SDK_URL`、`YUN_SDK_SHA256`、`YUN_SDK_SHA256SUMS_URL`（调试与镜像）。

### 4.3 `scripts/build_ext.py`

1. `ensure_sdk()` 取得 SDK；
2. `cmake -S <sdk> -B build/yun-sdk-binding`，传 `Python3_EXECUTABLE`、`pybind11_DIR`、`CMAKE_OSX_DEPLOYMENT_TARGET`、`CMAKE_OSX_ARCHITECTURES=arm64`、`CMAKE_SKIP_RPATH=ON`；
3. 构建 `yun_python_binding`；
4. 复制 `_core*.so` 到 `src/yunpyopt/`，清理旧版本并冒烟导入。

### 4.4 `pyproject.toml`

```toml
[build-system]
requires = ["poetry-core>=2.5,<3", "pybind11>=2.13,<4"]
build-backend = "poetry.core.masonry.api"

[tool.poetry.build]
script = "scripts/build_ext.py"
```

`cmake` 由宿主机提供（CI 的 macOS runner 预装，本地需安装）。

### 4.5 CI / Release

```yaml
- uses: actions/cache@v4
  with:
    path: ~/.cache/yunpyopt/sdk
    key: yun-sdk-${{ hashFiles('yun-sdk-version.txt') }}
```

`poetry install` 与 `python -m build` 触发 hook 下载并构建扩展；release 仍执行 `scripts/fix_wheel_tag.py` 修正平台标签。

---

## 5. 发布顺序（硬约束）

1. `yun` 发布 SDK Release（`v<yun-version>`）；
2. `yunpyopt` 更新 `yun-sdk-version.txt`（版本变化时）并 push；
3. `yunpyopt` 打 tag 发布 wheel。

SDK 不存在时，`fetch_sdk.py` 报错并提示先运行 `yun` 的 SDK Release workflow。

---

## 6. 约束

- **SDK 资产不可变**：同一版本不覆盖发布，否则 `SHA256SUMS` 变化影响复现；
- **ABI 匹配**：SDK 为 macOS arm64、C++20、部署目标 14.0，消费方必须一致；
- **头文件集合**：SDK 收集 binding 实际使用的 fmt/spdlog/yaml-cpp/magic_enum/libfork 头文件，升级这些依赖后需重新发布 SDK；
- **体积**：tarball 约 6.7 MB；
- **本地 Conan 缓存**：若部分依赖以更高 macOS 目标构建，链接会出现 "built for newer macOS" 警告；发布产物以全新 Conan 缓存的 CI 结果为准；
- **首次发布顺序**：必须先有 `yun` SDK Release，`yunpyopt` 的 CI/Release 才能通过。
