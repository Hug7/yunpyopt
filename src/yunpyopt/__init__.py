"""yunpyopt — Python caller for the project "yun".

Provides domain models for logistics optimization: locations, vehicles,
carriers, orders, distance matrices, and supporting dictionary types.
"""

from importlib.metadata import PackageNotFoundError, version
from typing import TYPE_CHECKING

from yunpyopt.domain.schema import (
    CargoOrder,
    CargoSubOrder,
    CargoSubOrderDimensionValue,
    CargoSubOrderLabelValue,
    Carrier,
    CarrierLabelValue,
    Dimension,
    DistMatrix,
    DistMatrixCode,
    Label,
    LabelApply,
    LabelApplyItem,
    LabelValue,
    Location,
    LocationAvailableVehicle,
    LocationLabelValue,
    Vehicle,
    VehicleModel,
    VehicleModelDimensionValue,
    VehicleModelLabelValue,
    WorkCalendarDaily,
    WorkCalendarWeekly,
    WorkEffect,
    WorkFixed,
)
from yunpyopt.domain.schema_model import SchemaModel

if TYPE_CHECKING:
    from yunpyopt.solver import (
        DEFAULT_LOG_LEVEL,
        RESULT_KEYS,
        SDK_PLATFORM,
        SDK_VERSION,
        Solver,
        SolveResult,
        YunSolverError,
        solve,
    )

try:
    __version__ = version("yunpyopt")
except PackageNotFoundError:  # pragma: no cover
    __version__ = "0.0.0"

_LAZY_SOLVER_EXPORTS = frozenset(
    {
        "Solver",
        "SolveResult",
        "YunSolverError",
        "DEFAULT_LOG_LEVEL",
        "RESULT_KEYS",
        "SDK_VERSION",
        "SDK_PLATFORM",
        "solve",
    }
)


def __getattr__(name: str) -> object:
    """延迟导入 solver，避免只用领域模型时强制加载二进制扩展。"""
    if name in _LAZY_SOLVER_EXPORTS:
        from . import solver

        return getattr(solver, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    "__version__",
    # base_dict
    "Dimension",
    "Label",
    "LabelApply",
    "LabelValue",
    "LabelApplyItem",
    # location
    "Location",
    "LocationAvailableVehicle",
    "LocationLabelValue",
    "WorkCalendarDaily",
    "WorkCalendarWeekly",
    "WorkEffect",
    "WorkFixed",
    # vehicle_model
    "VehicleModel",
    "VehicleModelDimensionValue",
    "VehicleModelLabelValue",
    # carrier
    "Carrier",
    "CarrierLabelValue",
    "Vehicle",
    # network
    "DistMatrixCode",
    "DistMatrix",
    # order
    "CargoOrder",
    "CargoSubOrder",
    "CargoSubOrderDimensionValue",
    "CargoSubOrderLabelValue",
    # SchemaModel
    "SchemaModel",
    # solver（按需加载）
    "Solver",
    "SolveResult",
    "YunSolverError",
    "DEFAULT_LOG_LEVEL",
    "RESULT_KEYS",
    "SDK_VERSION",
    "SDK_PLATFORM",
    "solve",
]
