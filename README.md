# yunpyopt

Python caller for the [`yun`](https://github.com/Hug7/yun) VRP/ALNS solver.

`yunpyopt` ships the pure-Python domain models plus the compiled `yunpyopt._core`
extension (pybind11) for in-process solving.

## Requirements

- macOS 14.0+ on Apple Silicon (`arm64`)
- CPython 3.11

The C++ code uses `std::format` and floating-point `std::to_chars`, which Apple's libc++
only provides from macOS 13.3. pip's macOS platform tags are major-version based
(`macosx_13_3` is not accepted on newer systems), so the wheel is tagged
`macosx_14_0_arm64` and requires macOS 14.0+.

## Install

This release is distributed as a GitHub Release wheel (PyPI is not enabled yet):

```bash
pip install https://github.com/Hug7/yunpyopt/releases/download/0.1.0/yunpyopt-0.1.0-cp311-cp311-macosx_14_0_arm64.whl
```

## Usage

```python
from pathlib import Path

from yunpyopt import solve

result = solve("path/to/c1_2_1", log_level="warning")
# {"loads": ".../Loads.json", "locations": ..., "unassigned": ..., "infeasible": None}

if result["loads"] is None:
    # precheck blocked the solve; inspect result["infeasible"]
    print("blocked:", result["infeasible"])
else:
    print(Path(result["loads"]))
```

`solve()` accepts `str` or `os.PathLike`, releases the GIL while solving, and can be
called repeatedly. A case directory needs the scenario CSVs and `Strategy.lua`, and
must be writable (`output/<request_id>/` is created under it).

## Build from source

Prerequisites: macOS 14.0+ arm64, Xcode Command Line Tools, CMake >= 3.15, Poetry,
Python 3.11.

```bash
git clone https://github.com/Hug7/yunpyopt.git
cd yunpyopt
poetry install
YUNPYOPT_REQUIRE_CORE=1 poetry run pytest -v
```

`poetry install` runs `scripts/build_ext.py` (a PEP 517 build hook). It downloads the
prebuilt `yun` SDK pinned by [`yun-sdk-version.txt`](yun-sdk-version.txt), builds the
pybind11 extension against it, and copies `_core*.so` into `src/yunpyopt/`. No `yun`
source checkout and no Conan are required.

To build against a locally built SDK:

```bash
YUN_SDK_DIR=/path/to/yun-sdk poetry install
```

The SDK itself is produced by [`yun`](https://github.com/Hug7/yun) with
`scripts/build_sdk.py` and attached to its GitHub Releases. The download is verified
against the release's `SHA256SUMS`; `YUN_SDK_VERSION` and `YUN_SDK_CACHE` can override
the pinned version and cache directory.

The generated `src/yunpyopt/_core*.so` is a build artifact: do not commit it, and do
not add it to any git ignore file (poetry-core would then exclude it from the wheel).

### Build a wheel

```bash
poetry build -f wheel
poetry run python scripts/fix_wheel_tag.py dist
```

`poetry-core` tags the wheel with the build interpreter's platform (for example
`macosx_11_0_arm64`). `scripts/fix_wheel_tag.py` reads the extension's
`LC_BUILD_VERSION` minos and rewrites the wheel tag to the actual minimum
(for example `macosx_14_0_arm64`). The release workflow does the same and validates
the result.

## Development

```bash
poetry run ruff check src tests
poetry run ruff format --check src tests
poetry run mypy src
YUNPYOPT_REQUIRE_CORE=1 poetry run pytest -v
```

Release process: [docs/release.md](docs/release.md).

## License

Apache-2.0
