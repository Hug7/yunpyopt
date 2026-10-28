# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] — Unreleased

### Added

- Domain schema dataclasses for logistics optimization:
  - `Dimension`, `Label`, `LabelValue`, `LabelApply` (base dictionaries)
  - `Location`, `LocationLabelValue`, `LocationAvailableVehicle`, `WorkCalendarDaily`, `WorkCalendarWeekly`, `WorkFixed`, `WorkEffect` (location)
  - `VehicleModel`, `VehicleModelDimensionValue`, `VehicleModelLabelValue` (vehicle models)
  - `Carrier`, `CarrierLabelValue`, `Vehicle` (carriers)
  - `DistMatrix` (route network)
  - `CargoOrder`, `CargoSubOrder`, `CargoSubOrderDimensionValue`, `CargoSubOrderLabelValue` (orders)
- Concise `__repr__` for all domain models
- Package-level `__version__` via `importlib.metadata`
- `py.typed` marker for PEP 561 compliance
- `typing-extensions` runtime dependency (for `typing.override` on Python 3.11)
- `yunpyopt.solver.solve()` / `Solver` for in-process calls into the `yun` solver
- Lazy `from yunpyopt import solve` export, so domain-only users do not need the binary
- `tests/data/c1_2_1` fixture and solver integration tests
- PEP 517 build hook (`scripts/build_ext.py`) that downloads the pinned prebuilt
  `yun` SDK (headers + monolithic static lib + binding source) and builds
  `yunpyopt._core` with pybind11
- `scripts/fetch_sdk.py` to download/verify/cache the SDK (`SHA256SUMS`)
- `scripts/fix_wheel_tag.py` to correct the wheel platform tag from the extension's
  actual `LC_BUILD_VERSION` minos
- GitHub Actions CI (macOS arm64, CPython 3.11) covering lint, typecheck, extension
  build, tests, wheel build/validation and a clean-venv install/solve
- `release.yml`: tag-driven wheel build and GitHub Release (PyPI publishing is not
  enabled yet)

### Changed

- `yun` SDK version is pinned in `yun-sdk-version.txt`; no `yun` source checkout or
  Conan is required in `yunpyopt`
- The wheel is platform-tagged (`cp311-cp311-macosx_14_0_arm64`) instead of the
  previous `py3-none-any`
- Supported platform is macOS 14.0+ arm64, CPython 3.11 (the C++ code uses
  `std::format`, which requires macOS 13.3; the wheel tag is rounded to 14_0 because
  pip's macOS tags are major-version based)
- `solver.solve()` accepts `PathLike`, validates result keys against the binding, and
  raises a clear `ImportError` if `yunpyopt._core` is missing
- Lint/typecheck configuration updated; `ruff` and `mypy` are clean

### Removed

- `yun` git submodule (`third_party/yun`)
- `yun`'s `BUILD_PY.sh` (hard-coded `python3.11` and the old `yunpy` output path);
  use `yun/scripts/build_python_extension.py` instead
