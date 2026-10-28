"""Domain schema package — all table-backed domain models."""

from .base_dict import Dimension, Label, LabelApply, LabelApplyItem, LabelValue
from .carrier import Carrier, CarrierLabelValue, Vehicle
from .location import (
    Location,
    LocationAvailableVehicle,
    LocationLabelValue,
    WorkCalendarDaily,
    WorkCalendarWeekly,
    WorkEffect,
    WorkFixed,
)
from .network import (
    DistMatrix,
    DistMatrixCode,
)
from .order import (
    CargoOrder,
    CargoSubOrder,
    CargoSubOrderDimensionValue,
    CargoSubOrderLabelValue,
)
from .vehicle_model import (
    VehicleModel,
    VehicleModelDimensionValue,
    VehicleModelLabelValue,
)

__all__ = [
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
]
