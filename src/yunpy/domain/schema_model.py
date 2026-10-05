from typing import List, Dict, Any, Set, Tuple

import pandas as pd

from .schema import Location, Dimension, Label, LabelValue, LabelApply, LocationLabelValue, LocationAvailableVehicle, \
    WorkCalendarDaily, WorkCalendarWeekly, WorkFixed, WorkEffect, DistMatrix, CargoOrder, CargoSubOrder, \
    CargoSubOrderDimensionValue, CargoSubOrderLabelValue, VehicleModel, VehicleModelDimensionValue, \
    VehicleModelLabelValue, Carrier, CarrierLabelValue, Vehicle, DistMatrixCode, LabelApplyItem


class DimensionManager:
    dimensions: List[Dimension]
    dimension_map: Dict[str, Dimension]

    def __init__(self):
        self.dimensions = []
        self.dimension_map = {}

    def add_dimension(self, dimension: Dimension):
        if self.dimension_map.__contains__(dimension.code):
            raise ValueError(f"Dimension {dimension.code} already exists")
        self.dimensions.append(dimension)
        self.dimension_map[dimension.code] = dimension

    def contains_dimension(self, code: str) -> bool:
        return self.dimension_map.__contains__(code)

    def to_csv(self, root_path: str) -> None:
        res_dimensions: List[Dict[str, Any]] = []
        if len(self.dimensions) == 0:
            res_dimensions.append(Dimension.empty_dict())
            raise ValueError('Dimension can not be empty')
        else:
            tmp_dimensions: List[Dimension] = list(self.dimensions)
            tmp_dimensions.sort()
            for dimension in tmp_dimensions:
                res_dimensions.append(dimension.to_dict())
        pd.DataFrame(res_dimensions).to_csv(f'{root_path}/{Dimension.table_name()}.csv', index=False)


class LabelManager:
    labels: Dict[str, Label]
    label_values: List[LabelValue]
    label_value_map: Dict[str, Set[str]]
    label_apples: List[LabelApply]
    item_label_map: Dict[str, Set[str]]

    def __init__(self):
        self.labels = {}
        self.label_values = []
        self.label_value_map = {}
        self.label_apples = []
        self.item_label_map = {}

    def contains_label(self, label_code: str) -> bool:
        return self.labels.__contains__(label_code)

    def contains_label_value(self, label_code: str, label_value: str) -> bool:
        if not self.contains_label(label_code):
            raise ValueError(f"Label {label_code} not exists")
        return self.label_value_map[label_code].__contains__(label_value)

    def add_label(self, label: Label):
        if self.contains_label(label.code):
            raise ValueError(f"Label {label.code} already exists")
        self.labels[label.code] = label
        self.label_value_map[label.code] = set()

    def add_label_value(self, label_value: LabelValue):
        if not self.contains_label(label_value.label_code):
            raise ValueError(f"Label {label_value.label_code} not exists")
        if self.label_value_map[label_value.label_code].__contains__(label_value.label_value):
            raise ValueError(f"Label value {label_value.label_value} already exists for Label {label_value.label_code}")
        self.label_values.append(label_value)
        self.label_value_map[label_value.label_code].add(label_value.label_value)

    def add_label_apply(self, label_apply: LabelApply):
        if not self.contains_label(label_apply.label_code):
            raise ValueError(f"Label {label_apply.label_code} not exists")
        if not self.item_label_map.__contains__(label_apply.apply_item):
            self.item_label_map[label_apply.apply_item] = set()
        if self.item_label_map[label_apply.apply_item].__contains__(label_apply.label_code):
            raise ValueError(f"Label {label_apply.label_code} already apply to item {label_apply.apply_item}")

        self.item_label_map[label_apply.apply_item].add(label_apply.label_code)
        self.label_apples.append(label_apply)

    def to_csv(self, root_path: str):
        # to label csv
        label_file_path = f'{root_path}/{Label.table_name()}.csv'
        if len(self.labels) == 0:
            pd.DataFrame([], columns=Label.columns()).to_csv(label_file_path, index=False)
        else:
            tmp_labels: List[Label] = list(self.labels.values())
            tmp_labels.sort()
            res_labels: List[Dict[str, Any]] = []
            for label in tmp_labels:
                res_labels.append(label.to_dict())

            pd.DataFrame(res_labels).to_csv(label_file_path, index=False)

        # to label value csv
        label_value_file_path = f'{root_path}/{LabelValue.table_name()}.csv'
        if len(self.label_values) == 0:
            pd.DataFrame([], columns=LabelValue.columns()).to_csv(label_value_file_path, index=False)
        else:
            tmp_label_values = list(self.label_values)
            tmp_label_values.sort()
            res_label_values: List[Dict[str, Any]] = []
            for label_value in tmp_label_values:
                res_label_values.append(label_value.to_dict())
            pd.DataFrame(res_label_values).to_csv(label_value_file_path, index=False)

        # to label apply csv
        label_apply_file_path = f'{root_path}/{LabelApply.table_name()}.csv'
        if len(self.item_label_map) == 0:
            pd.DataFrame([], columns=LabelApply.columns()).to_csv(label_apply_file_path, index=False)
        else:
            tmp_label_apples = list(self.label_apples)
            tmp_label_apples.sort()
            res_label_apples: List[Dict[str, Any]] = []
            for label_apple in tmp_label_apples:
                res_label_apples.append(label_apple.to_dict())
            pd.DataFrame.from_dict(res_label_apples).to_csv(label_apply_file_path, index=False)


class CargoOrderManager:
    cargo_orders: Dict[str, CargoOrder]
    cargo_sub_orders: Dict[str, Dict[str, CargoSubOrder]]
    cargo_sub_order_dimension_values: Set[CargoSubOrderDimensionValue]
    cargo_sub_order_label_values: Set[CargoSubOrderLabelValue]

    def __init__(self):
        self.cargo_orders = {}
        self.cargo_sub_orders = {}
        self.cargo_sub_order_dimension_values = set()
        self.cargo_sub_order_label_values = set()

    def contains_cargo_order(self, cargo_order_code: str) -> bool:
        return self.cargo_orders.__contains__(cargo_order_code)

    def contains_cargo_sub_order(self, cargo_order_code: str, cargo_sub_order_code: str) -> bool:
        if not self.contains_cargo_order(cargo_order_code):
            return False
        if not self.cargo_sub_orders[cargo_order_code].__contains__(cargo_sub_order_code):
            return False

        return True

    def add_cargo_order(self, cargo_order: CargoOrder):
        if self.contains_cargo_order(cargo_order.code):
            raise ValueError(f"Cargo order {cargo_order.code} already exists in {CargoSubOrder.table_name()}")

        # todo check datetime format

        self.cargo_orders[cargo_order.code] = cargo_order
        self.cargo_sub_orders[cargo_order.code] = {}

    def add_cargo_sub_order(self, cargo_sub_order: CargoSubOrder):
        cargo_order_code = cargo_sub_order.cargo_order_code
        if not self.contains_cargo_order(cargo_order_code):
            raise ValueError(f"Cargo order code {cargo_order_code} not exists in {CargoSubOrder.table_name()}")
        cargo_sub_order_code = cargo_sub_order.cargo_sub_order_code
        if self.contains_cargo_sub_order(cargo_order_code, cargo_sub_order_code):
            raise ValueError(f"Cargo order code {cargo_order_code} cargo sub order code {cargo_sub_order_code} "
                             f"already exists in {CargoSubOrder.table_name()}")
        if cargo_sub_order.quantity <= 0:
            raise ValueError(f"Cargo order code {cargo_order_code} cargo sub order code {cargo_sub_order_code} "
                             f"quantity {cargo_sub_order.quantity} should be greater than 0 "
                             f"in {CargoSubOrder.table_name()}")

        self.cargo_sub_orders[cargo_order_code][cargo_sub_order_code] = cargo_sub_order

    def add_cargo_sub_order_dimension_value(self, cargo_sub_order_dimension_value: CargoSubOrderDimensionValue):
        cargo_order_code = cargo_sub_order_dimension_value.cargo_order_code
        if not self.contains_cargo_order(cargo_order_code):
            raise ValueError(f"Cargo order code {cargo_order_code} not exists in cargo sub order dimension value")
        cargo_sub_order_code = cargo_sub_order_dimension_value.cargo_sub_order_code
        if not self.contains_cargo_sub_order(cargo_order_code, cargo_sub_order_code):
            raise ValueError(f"Cargo order code {cargo_order_code} cargo sub order code {cargo_sub_order_code} "
                             f"not exists in cargo sub order dimension value")

        if self.cargo_sub_order_dimension_values.__contains__(cargo_sub_order_dimension_value):
            raise ValueError(f"Cargo order code {cargo_order_code} cargo sub order code {cargo_sub_order_code} "
                             f"dimension code {cargo_sub_order_dimension_value.dimension_code} "
                             f"already exists in cargo sub order dimension value")

        self.cargo_sub_order_dimension_values.add(cargo_sub_order_dimension_value)

    def add_cargo_sub_order_label_value(self, cargo_sub_order_label_value: CargoSubOrderLabelValue):
        cargo_order_code = cargo_sub_order_label_value.cargo_order_code
        if not self.contains_cargo_order(cargo_order_code):
            raise ValueError(
                f"Cargo order code {cargo_order_code} not exists in {CargoSubOrderLabelValue.table_name()}")
        cargo_sub_order_code = cargo_sub_order_label_value.cargo_sub_order_code
        if self.contains_cargo_sub_order(cargo_order_code, cargo_sub_order_code):
            raise ValueError(f"Cargo order code {cargo_order_code} cargo sub order code {cargo_sub_order_code} "
                             f"already exists in {CargoSubOrderLabelValue.table_name()}")

        if self.cargo_sub_order_label_values.__contains__(cargo_sub_order_label_value):
            raise ValueError(f"Cargo order code {cargo_order_code} cargo sub order code {cargo_sub_order_code} "
                             f"label code {cargo_sub_order_label_value.label_code} "
                             f"label value {cargo_sub_order_label_value.label_value} "
                             f"already exists in {CargoSubOrderLabelValue.table_name()}")

        self.cargo_sub_order_label_values.add(cargo_sub_order_label_value)

    def to_csv(self, root_path: str):
        # to cargo order csv
        if len(self.cargo_orders) == 0:
            raise ValueError(f"{CargoOrder.table_name()} can not be empty")
        res_cargo_orders: List[Dict[str, Any]] = []
        tmp_cargo_orders = list(self.cargo_orders.values())
        tmp_cargo_orders.sort()
        for cargo_order in tmp_cargo_orders:
            res_cargo_orders.append(cargo_order.to_dict())

        pd.DataFrame.from_dict(res_cargo_orders).to_csv(f'{root_path}/{CargoOrder.table_name()}.csv', index=False)

        # to cargo sub order csv
        if len(self.cargo_sub_orders) == 0:
            raise ValueError(f"{CargoSubOrder.table_name()} can not be empty")
        tmp_cargo_sub_orders: List[CargoSubOrder] = []
        for cargo_order_code, group_cargo_sub_orders in self.cargo_sub_orders.items():
            if len(group_cargo_sub_orders) == 0:
                raise ValueError(f"{CargoSubOrder.table_name()} can not be empty for cargo order code {cargo_order_code}")
            for _, cargo_sub_order in group_cargo_sub_orders.items():
                tmp_cargo_sub_orders.append(cargo_sub_order)
        tmp_cargo_sub_orders.sort()
        res_cargo_sub_orders: List[Dict[str, Any]] = []
        for cargo_sub_order in tmp_cargo_sub_orders:
            res_cargo_sub_orders.append(cargo_sub_order.to_dict())
        pd.DataFrame.from_dict(res_cargo_sub_orders).to_csv(f'{root_path}/{CargoSubOrder.table_name()}.csv',
                                                            index=False)

        # to cargo sub order dimension value csv
        cargo_sub_order_dimension_value_file_path = f'{root_path}/{CargoSubOrderDimensionValue.table_name()}.csv'
        if len(self.cargo_sub_order_dimension_values) == 0:
            pd.DataFrame([], columns=CargoSubOrderDimensionValue.columns()).to_csv(
                cargo_sub_order_dimension_value_file_path, index=False)
        else:
            tmp_cargo_sub_order_dimension_values = list(self.cargo_sub_order_dimension_values)
            tmp_cargo_sub_order_dimension_values.sort()
            res_cargo_sub_order_dimension_values: List[Dict[str, Any]] = []
            for cargo_sub_order_dimension_value in tmp_cargo_sub_order_dimension_values:
                res_cargo_sub_order_dimension_values.append(cargo_sub_order_dimension_value.to_dict())

            pd.DataFrame.from_dict(res_cargo_sub_order_dimension_values).to_csv(
                cargo_sub_order_dimension_value_file_path, index=False)

        # to cargo sub order label value csv
        cargo_sub_order_label_value_file_path = f'{root_path}/{CargoSubOrderLabelValue.table_name()}.csv'
        if len(self.cargo_sub_order_label_values) == 0:
            pd.DataFrame([], columns=CargoSubOrderLabelValue.columns()).to_csv(
                cargo_sub_order_label_value_file_path, index=False)
        else:
            tmp_cargo_sub_order_label_values = list(self.cargo_sub_order_label_values)
            tmp_cargo_sub_order_label_values.sort()
            res_cargo_sub_order_label_values: List[Dict[str, Any]] = []
            for cargo_sub_order_label_value in tmp_cargo_sub_order_label_values:
                res_cargo_sub_order_label_values.append(cargo_sub_order_label_value.to_dict())

            pd.DataFrame.from_dict(res_cargo_sub_order_label_values).to_csv(
                cargo_sub_order_label_value_file_path, index=False)


class LocationManager:
    locations: Dict[str, Location]
    location_label_values: Set[LocationLabelValue]
    location_available_vehicles: Set[LocationAvailableVehicle]
    work_calendar_map: Dict[str, Set[str]]
    work_calendar_dailies: Set[WorkCalendarDaily]
    work_calendar_weeklies: Set[WorkCalendarWeekly]
    work_fixed_set: Set[WorkFixed]
    work_effect_set: Set[WorkEffect]

    def __init__(self):
        self.locations = {}
        self.location_label_values = set()
        self.location_available_vehicles = set()
        self.work_calendar_map = {}
        self.work_calendar_dailies = set()
        self.work_calendar_weeklies = set()
        self.work_fixed_set = set()
        self.work_effect_set = set()

    def contains_location(self, location_code: str) -> bool:
        return self.locations.__contains__(location_code)

    def add_location(self, location: Location):
        if self.contains_location(location.code):
            raise ValueError(f"Location {location.code} already exists")
        self.locations[location.code] = location
        self.work_calendar_map[location.code] = set()

    def add_location_label_value(self, location_label_value: LocationLabelValue):
        if not self.contains_location(location_label_value.location_code):
            raise ValueError(
                f"Location {location_label_value.location_code} not exists in {LocationLabelValue.table_name()}")

        if self.location_label_values.__contains__(location_label_value.label_code):
            raise ValueError(f"Location {location_label_value.location_code} "
                             f"label {location_label_value.label_code} "
                             f"label value {location_label_value.label_value} is repeated "
                             f"in {LocationLabelValue.table_name()}")

        self.location_label_values.add(location_label_value)

    def add_location_available_vehicle(self, location_available_vehicle: LocationAvailableVehicle):
        if not self.contains_location(location_available_vehicle.location_code):
            raise ValueError(
                f"Location {location_available_vehicle.location_code} not exists in {LocationAvailableVehicle.table_name()}")

        if self.location_available_vehicles.__contains__(location_available_vehicle):
            raise ValueError(f"Location {location_available_vehicle.location_code} "
                             f"carrier {location_available_vehicle.carrier_code} "
                             f"vehicle model {location_available_vehicle.vehicle_model_code} is repeated "
                             f"in {LocationAvailableVehicle.table_name()}")

        self.location_available_vehicles.add(location_available_vehicle)

    def add_work_calendar_daily(self, work_calendar_daily: WorkCalendarDaily):
        cur_location_code = work_calendar_daily.location_code
        cur_calendar_type = work_calendar_daily.calendar_type
        if not self.contains_location(cur_location_code):
            raise ValueError(f"Location {cur_location_code} not exists in {WorkCalendarDaily.table_name()}")
        if self.work_calendar_dailies.__contains__(work_calendar_daily):
            raise ValueError(
                f"Location {cur_location_code} calendar_type {cur_calendar_type} is repeated in {WorkCalendarDaily.table_name()}")
        if self.work_calendar_map[cur_location_code].__contains__(cur_calendar_type):
            raise ValueError(f"Location {cur_location_code} calendar_type {cur_calendar_type} "
                             f"has already been defined by work calendar weekly in {WorkCalendarDaily.table_name()}")

        self.work_calendar_dailies.add(work_calendar_daily)
        self.work_calendar_map[cur_location_code].add(cur_calendar_type)

    def add_work_calendar_weekly(self, work_calendar_weekly: WorkCalendarWeekly):
        cur_location_code = work_calendar_weekly.location_code
        cur_calendar_type = work_calendar_weekly.calendar_type
        if not self.contains_location(cur_location_code):
            raise ValueError(f"Location {cur_location_code} not exists in {WorkCalendarWeekly.table_name()}")
        if self.work_calendar_weeklies.__contains__(work_calendar_weekly):
            raise ValueError(
                f"Location {cur_location_code} calendar_type {cur_calendar_type} is repeated in {WorkCalendarWeekly.table_name()}")
        if self.work_calendar_map[cur_location_code].__contains__(cur_calendar_type):
            raise ValueError(f"Location {cur_location_code} calendar_type {cur_calendar_type} "
                             f"has already been defined by work calendar daily in {WorkCalendarWeekly.table_name()}")

        self.work_calendar_weeklies.add(work_calendar_weekly)
        self.work_calendar_map[cur_location_code].add(cur_calendar_type)

    def add_work_fixed(self, work_fixed: WorkFixed):
        if not self.contains_location(work_fixed.location_code):
            raise ValueError(f"Location {work_fixed.location_code} not exists in {WorkFixed.table_name()}")
        if self.work_fixed_set.__contains__(work_fixed):
            raise ValueError(f"Location {work_fixed.location_code} is repeated in {WorkFixed.table_name()}")

        self.work_fixed_set.add(work_fixed)

    def add_work_effect(self, work_effect: WorkEffect):
        if not self.contains_location(work_effect.location_code):
            raise ValueError(f"Location {work_effect.location_code} not exists in {WorkEffect.table_name()}")
        if self.work_effect_set.__contains__(work_effect):
            raise ValueError(f"Location {work_effect.location_code} is repeated in {WorkEffect.table_name()}")

        self.work_effect_set.add(work_effect)

    def to_csv(self, root_path: str):
        # location to csv
        res_locations: List[Dict[str, Any]] = []
        if len(self.locations) == 0:
            raise ValueError(f"Location can not be empty")
        else:
            for _, location in self.locations.items():
                res_locations.append(location.to_dict())
        pd.DataFrame.from_dict(res_locations).to_csv(f'{root_path}/{Location.table_name()}.csv', index=False)
        # location label value to csv
        location_label_value_file_path = f'{root_path}/{LocationLabelValue.table_name()}.csv'
        if len(self.location_label_values) == 0:
            pd.DataFrame([], columns=LocationLabelValue.columns()).to_csv(location_label_value_file_path, index=False)
        else:
            res_location_label_values: List[Dict[str, Any]] = []
            for location_label_value in self.location_label_values:
                res_location_label_values.append(location_label_value.to_dict())
            pd.DataFrame.from_dict(res_location_label_values).to_csv(location_label_value_file_path, index=False)
        # location available vehicle to csv
        location_available_vehicle_file_path = f'{root_path}/{LocationAvailableVehicle.table_name()}.csv'
        if len(self.location_available_vehicles) == 0:
            pd.DataFrame([], columns=LocationAvailableVehicle.columns()).to_csv(location_available_vehicle_file_path, index=False)
        else:
            res_location_available_vehicles: List[Dict[str, Any]] = []
            for location_available_vehicle in self.location_available_vehicles:
                res_location_available_vehicles.append(location_available_vehicle.to_dict())
            pd.DataFrame.from_dict(res_location_available_vehicles).to_csv(location_available_vehicle_file_path, index=False)
        # location work calendar daily to csv
        work_calendar_daily_file_path = f'{root_path}/{WorkCalendarDaily.table_name()}.csv'
        if len(self.work_calendar_dailies) == 0:
            pd.DataFrame([], columns=WorkCalendarDaily.columns()).to_csv(work_calendar_daily_file_path, index=False)
        else:
            res_work_calendar_dailies: List[Dict[str, Any]] = []
            for work_calendar_daily in self.work_calendar_dailies:
                res_work_calendar_dailies.append(work_calendar_daily.to_dict())
            pd.DataFrame.from_dict(res_work_calendar_dailies).to_csv(work_calendar_daily_file_path, index=False)
        # location work calendar weekly to csv
        work_calendar_weekly_file_path = f'{root_path}/{WorkCalendarWeekly.table_name()}.csv'
        if len(self.work_calendar_weeklies) == 0:
            pd.DataFrame([], columns=WorkCalendarWeekly.columns()).to_csv(work_calendar_weekly_file_path, index=False)
        else:
            res_work_calendar_weeklies: List[Dict[str, Any]] = []
            for work_calendar_weekly in self.work_calendar_weeklies:
                res_work_calendar_weeklies.append(work_calendar_weekly.to_dict())
            pd.DataFrame.from_dict(res_work_calendar_weeklies).to_csv(work_calendar_weekly_file_path, index=False)
        # location work fixed
        work_fixed_file_path = f'{root_path}/{WorkFixed.table_name()}.csv'
        if len(self.work_fixed_set) == 0:
            pd.DataFrame([], columns=WorkFixed.columns()).to_csv(work_fixed_file_path, index=False)
        else:
            res_work_fixeds: List[Dict[str, Any]] = []
            for work_fixed_map in self.work_fixed_set:
                res_work_fixeds.append(work_fixed_map.to_dict())
            pd.DataFrame.from_dict(res_work_fixeds).to_csv(work_fixed_file_path, index=False)
        # location work effect
        work_effect_file_path = f'{root_path}/{WorkEffect.table_name()}.csv'
        if len(self.work_effect_set) == 0:
            pd.DataFrame([], columns=WorkEffect.columns()).to_csv(work_effect_file_path, index=False)
        else:
            res_work_effects: List[Dict[str, Any]] = []
            for work_effect in self.work_effect_set:
                res_work_effects.append(work_effect.to_dict())
            pd.DataFrame.from_dict(res_work_effects).to_csv(work_effect_file_path, index=False)


class NetWorkManager:
    dist_matrix_codes: Dict[str, DistMatrixCode]
    dist_matrices: Dict[str, Dict[str, Dict[str, DistMatrix]]]

    def __init__(self):
        self.dist_matrix_codes = {}
        self.dist_matrices = {}

    def contains_dist_matrix_code(self, dist_matrix_code: str):
        return self.dist_matrix_codes.__contains__(dist_matrix_code)

    def add_dist_matrix_code(self, dist_matrix_code: DistMatrixCode):
        cur_dist_matrix_code = dist_matrix_code.code
        if self.contains_dist_matrix_code(cur_dist_matrix_code):
            raise ValueError(f"Dist matrix code {cur_dist_matrix_code} already exists in {DistMatrixCode.table_name()}")

        self.dist_matrix_codes[cur_dist_matrix_code] = dist_matrix_code
        self.dist_matrices[cur_dist_matrix_code] = {}

    def add_dist_matrix(self, dist_matrix: DistMatrix):
        cur_dist_matrix_code = dist_matrix.dist_matrix_code
        if not self.contains_dist_matrix_code(cur_dist_matrix_code):
            raise ValueError(f"Dist matrix code {cur_dist_matrix_code} not exists in {DistMatrixCode.table_name()}")

        from_loc_code = dist_matrix.from_location_code
        to_loc_code = dist_matrix.to_location_code

        if not self.dist_matrices[cur_dist_matrix_code].__contains__(from_loc_code):
            self.dist_matrices[cur_dist_matrix_code][from_loc_code] = dict()
        if self.dist_matrices[cur_dist_matrix_code][from_loc_code].__contains__(to_loc_code):
            raise ValueError(f"Dist matrix code {cur_dist_matrix_code} "
                             f"from location code {from_loc_code} "
                             f"to location code {to_loc_code} already exists in {DistMatrixCode.table_name()}")

        self.dist_matrices[cur_dist_matrix_code][from_loc_code][to_loc_code] = dist_matrix

    def to_csv(self, root_path: str):
        if len(self.dist_matrix_codes) == 0:
            raise ValueError(f"Dist matrix codes can not be empty")
        res_dist_matrix_codes: List[Dict[str, Any]] = []
        for _, dist_matrix_code in self.dist_matrix_codes.items():
            res_dist_matrix_codes.append(dist_matrix_code.to_dict())

        pd.DataFrame.from_dict(res_dist_matrix_codes).to_csv(f'{root_path}/{DistMatrixCode.table_name()}.csv',
                                                             index=False)

        # todo check integrity of dist matrix

        res_dist_matrices: List[Dict[str, Any]] = []
        for _, f_t_dist_matrices in self.dist_matrices.items():
            for _, t_dist_matrices in f_t_dist_matrices.items():
                for _, dist_matrix in t_dist_matrices.items():
                    res_dist_matrices.append(dist_matrix.to_dict())

        pd.DataFrame.from_dict(res_dist_matrices).to_csv(f'{root_path}/{DistMatrix.table_name()}.csv', index=False)


class VehicleModelManager:
    vehicle_models: Dict[str, VehicleModel]
    vehicle_model_dimension_values: Set[VehicleModelDimensionValue]
    vehicle_model_label_values: Set[VehicleModelLabelValue]

    def __init__(self):
        self.vehicle_models = {}
        self.vehicle_model_dimension_values = set()
        self.vehicle_model_label_values = set()

    def contains_vehicle_model(self, vehicle_model_code: str):
        return self.vehicle_models.__contains__(vehicle_model_code)

    def add_vehicle_model(self, vehicle_model: VehicleModel):
        if self.contains_vehicle_model(vehicle_model.code):
            raise ValueError(f"Vehicle model code {vehicle_model.code} already exists in {VehicleModel.table_name()}")

        self.vehicle_models[vehicle_model.code] = vehicle_model

    def add_vehicle_model_dimension_value(self, vehicle_model_dimension: VehicleModelDimensionValue):
        if self.vehicle_model_dimension_values.__contains__(vehicle_model_dimension):
            raise ValueError(f"Vehicle model {vehicle_model_dimension.vehicle_model_code} "
                             f"dimension {vehicle_model_dimension.dimension_code} already exists "
                             f"in {VehicleModelDimensionValue.table_name()}")

        self.vehicle_model_dimension_values.add(vehicle_model_dimension)

    def add_vehicle_model_label_value(self, vehicle_model_label: VehicleModelLabelValue):
        if self.vehicle_model_label_values.__contains__(vehicle_model_label):
            raise ValueError(f"Vehicle model {vehicle_model_label.vehicle_model_code} "
                             f"label {vehicle_model_label.label_code} "
                             f"label value {vehicle_model_label.label_value} already exists "
                             f"in {VehicleModelLabelValue.table_name()}")

        self.vehicle_model_label_values.add(vehicle_model_label)

    def to_csv(self, root_path: str):
        # to vehicle model csv
        if len(self.vehicle_models) == 0:
            raise ValueError(f"Vehicle models can not be empty")
        tmp_vehicle_models = list(self.vehicle_models.values())
        tmp_vehicle_models.sort()
        res_vehicle_models: List[Dict[str, Any]] = []
        for vehicle_model in tmp_vehicle_models:
            res_vehicle_models.append(vehicle_model.to_dict())

        pd.DataFrame.from_dict(res_vehicle_models).to_csv(f'{root_path}/{VehicleModel.table_name()}.csv', index=False)

        # to vehicle model dimension value csv
        vehicle_model_dimension_value_file_path = f'{root_path}/{VehicleModelDimensionValue.table_name()}.csv'
        if len(self.vehicle_model_dimension_values) == 0:
            pd.DataFrame([], columns=VehicleModelDimensionValue.columns()).to_csv(
                vehicle_model_dimension_value_file_path, index=False)
        else:
            tmp_vehicle_model_dimension_values: List[VehicleModelDimensionValue] = list(self.vehicle_model_dimension_values)
            tmp_vehicle_model_dimension_values.sort()
            res_vehicle_model_dimension_values: List[Dict[str, Any]] = []
            for vehicle_model_dimension_value in tmp_vehicle_model_dimension_values:
                res_vehicle_model_dimension_values.append(vehicle_model_dimension_value.to_dict())

            pd.DataFrame.from_dict(res_vehicle_model_dimension_values).to_csv(
                vehicle_model_dimension_value_file_path, index=False)

        # to vehicle model label value csv
        vehicle_model_label_value_file_path = f'{root_path}/{VehicleModelLabelValue.table_name()}.csv'
        if len(self.vehicle_model_label_values) == 0:
            pd.DataFrame([], columns=VehicleModelLabelValue.columns()).to_csv(
                vehicle_model_label_value_file_path, index=False)
        else:
            tmp_vehicle_model_label_values: List[VehicleModelLabelValue] = list(self.vehicle_model_label_values)
            tmp_vehicle_model_label_values.sort()
            res_vehicle_model_label_values: List[Dict[str, Any]] = []
            for vehicle_model_label_value in tmp_vehicle_model_label_values:
                res_vehicle_model_label_values.append(vehicle_model_label_value.to_dict())

            pd.DataFrame.from_dict(res_vehicle_model_label_values).to_csv(
                vehicle_model_label_value_file_path, index=False)


class CarrierManager:
    carriers: Dict[str, Carrier]
    carrier_label_values: Set[CarrierLabelValue]
    vehicles: Set[Vehicle]

    def __init__(self):
        self.carriers = {}
        self.carrier_label_values = set()
        self.vehicles = set()

    def contains_carrier(self, carrier_code: str):
        return self.carriers.__contains__(carrier_code)

    def add_carrier(self, carrier: Carrier):
        if self.contains_carrier(carrier.code):
            raise ValueError(f"Carrier code {carrier.code} already exists in {Carrier.table_name()}")

        self.carriers[carrier.code] = carrier

    def add_carrier_label_value(self, carrier_label: CarrierLabelValue):
        if not self.carrier_label_values.__contains__(carrier_label):
            raise ValueError(f"Carrier code {carrier_label.carrier_code} not exists "
                             f"in {CarrierLabelValue.table_name()}")

        if self.carrier_label_values.__contains__(carrier_label):
            raise ValueError(f"Carrier code {carrier_label.carrier_code} "
                             f"label code {carrier_label.label_code} "
                             f"label value {carrier_label.label_value} "
                             f"already exists in {CarrierLabelValue.table_name()}")

        self.carrier_label_values.add(carrier_label)

    def add_vehicle(self, vehicle: Vehicle):
        carrier_code: str = vehicle.carrier_code
        if not self.contains_carrier(carrier_code):
            raise ValueError(f"Carrier code {carrier_code} not exists in {Vehicle.table_name()}")

        if self.vehicles.__contains__(vehicle):
            raise ValueError(f"Carrier code {vehicle.carrier_code} "
                             f"vehicle model code {vehicle.vehicle_model_code} "
                             f"origin location code {vehicle.get_origin_location_code()} "
                             f"destination location code {vehicle.get_destination_location_code()} "
                             f"is repeated in {Vehicle.table_name()}")

        self.vehicles.add(vehicle)

    def to_csv(self, root_path: str):
        # to carrier csv
        if len(self.carriers) == 0:
            raise ValueError(f"Carriers can not be empty")
        tmp_carriers = list(self.carriers.values())
        tmp_carriers.sort()
        res_carriers: List[Dict[str, Any]] = []
        for carrier in tmp_carriers:
            res_carriers.append(carrier.to_dict())

        pd.DataFrame.from_dict(res_carriers).to_csv(f'{root_path}/{Carrier.table_name()}.csv', index=False)

        # to carrier label value csv
        carrier_label_value_file_path = f'{root_path}/{CarrierLabelValue.table_name()}.csv'
        if len(self.carrier_label_values) == 0:
            pd.DataFrame([], columns=CarrierLabelValue.columns()).to_csv(
                carrier_label_value_file_path, index=False)
        else:
            tmp_carrier_label_values = list(self.carrier_label_values)
            tmp_carrier_label_values.sort()
            res_carrier_label_values: List[Dict[str, Any]] = []
            for carrier_label_value in tmp_carrier_label_values:
                res_carrier_label_values.append(carrier_label_value.to_dict())

            pd.DataFrame.from_dict(res_carrier_label_values).to_csv(carrier_label_value_file_path, index=False)

        # to vehicle csv
        if len(self.vehicles) == 0:
            raise ValueError(f"Vehicles can not be empty")
        res_vehicles: List[Dict[str, Any]] = []
        for vehicle in self.vehicles:
            res_vehicles.append(vehicle.to_dict())

        pd.DataFrame.from_dict(res_vehicles).to_csv(f'{root_path}/{Vehicle.table_name()}.csv', index=False)

class SchemaModel:
    dimension_manager: DimensionManager
    label_manager: LabelManager
    location_manager: LocationManager
    carrier_manager: CarrierManager
    vehicle_model_manager: VehicleModelManager
    net_work_manager: NetWorkManager
    cargo_order_manager: CargoOrderManager

    def __init__(self):
        self.dimension_manager = DimensionManager()
        self.label_manager = LabelManager()
        self.location_manager = LocationManager()
        self.carrier_manager = CarrierManager()
        self.vehicle_model_manager = VehicleModelManager()
        self.net_work_manager = NetWorkManager()
        self.cargo_order_manager = CargoOrderManager()

    def add_dimension(self, dimension: Dimension):
        self.dimension_manager.add_dimension(dimension)

    def add_label(self, label: Label):
        self.label_manager.add_label(label)

    def add_label_value(self, label_value: LabelValue):
        self.label_manager.add_label_value(label_value)

    def add_label_apply(self, label_apply: LabelApply):
        self.label_manager.add_label_apply(label_apply)

    def add_location(self, location: Location):
        self.location_manager.add_location(location)

    def add_location_label_value(self, location_label_value: LocationLabelValue):
        if self.label_manager.contains_label(location_label_value.label_code):
            raise ValueError(f"Label {location_label_value.label_code} not exists "
                             f"in {LocationLabelValue.table_name()}")
        if self.label_manager.contains_label_value(location_label_value.label_code, location_label_value.label_value):
            raise ValueError(f"Label {location_label_value.label_code} "
                             f"label value {location_label_value.label_value} not exists "
                             f"in {LocationLabelValue.table_name()}")

        self.location_manager.add_location_label_value(location_label_value)

    def add_location_available_vehicle(self, location_available_vehicle: LocationAvailableVehicle):
        if not self.location_manager.contains_location(location_available_vehicle.location_code):
            raise ValueError(f"Location {location_available_vehicle.location_code} not exists "
                             f"in {LocationAvailableVehicle.table_name()}")
        if not self.carrier_manager.contains_carrier(location_available_vehicle.carrier_code):
            raise ValueError(f"Carrier {location_available_vehicle.carrier_code} not exists "
                             f"in {LocationAvailableVehicle.table_name()}")
        if not self.vehicle_model_manager.contains_vehicle_model(location_available_vehicle.vehicle_model_code):
            raise ValueError(f"Vehicle Model {location_available_vehicle.vehicle_model_code} not exists "
                             f"in {LocationAvailableVehicle.table_name()}")

        self.location_manager.add_location_available_vehicle(location_available_vehicle)

    def add_work_calendar_daily(self, work_calendar_daily: WorkCalendarDaily):
        self.location_manager.add_work_calendar_daily(work_calendar_daily)

    def add_work_calendar_weekly(self, work_calendar_weekly: WorkCalendarWeekly):
        self.location_manager.add_work_calendar_weekly(work_calendar_weekly)

    def add_work_fixed(self, work_fixed: WorkFixed):
        self.location_manager.add_work_fixed(work_fixed)

    def add_work_effect(self, work_effect: WorkEffect):
        self.location_manager.add_work_effect(work_effect)

    def add_dist_matrix_code(self, dist_matrix_code: DistMatrixCode):
        self.net_work_manager.add_dist_matrix_code(dist_matrix_code)

    def add_vehicle_model(self, vehicle_model: VehicleModel):
        if not self.net_work_manager.contains_dist_matrix_code(vehicle_model.dist_matrix_code):
            raise ValueError(f"Dist matrix {vehicle_model.dist_matrix_code} not exists in {VehicleModel.table_name()}")

        self.vehicle_model_manager.add_vehicle_model(vehicle_model)

    def add_vehicle_model_dimension_value(self, vehicle_model_dimension_value: VehicleModelDimensionValue):
        if not self.dimension_manager.contains_dimension(vehicle_model_dimension_value.dimension_code):
            raise ValueError(f"Dimension {vehicle_model_dimension_value.dimension_code} not exists "
                             f"in {VehicleModelDimensionValue.table_name()}")

        self.vehicle_model_manager.add_vehicle_model_dimension_value(vehicle_model_dimension_value)

    def add_vehicle_model_label_value(self, vehicle_model_label_value: VehicleModelLabelValue):
        if not self.label_manager.contains_label(vehicle_model_label_value.label_code):
            raise ValueError(f"Label {vehicle_model_label_value.label_code} not exists "
                             f"in {VehicleModelLabelValue.table_name()}")
        if not self.label_manager.contains_label_value(vehicle_model_label_value.label_code,
                                                       vehicle_model_label_value.label_value):
            raise ValueError(f"Label {vehicle_model_label_value.label_code} "
                             f"label value {vehicle_model_label_value.label_value} not exists "
                             f"in {VehicleModelLabelValue.table_name()}")

        self.vehicle_model_manager.add_vehicle_model_label_value(vehicle_model_label_value)

    def add_dist_matrix(self, dist_matrix: DistMatrix):
        if not self.location_manager.contains_location(dist_matrix.from_location_code):
            raise ValueError(f"Location {dist_matrix.from_location_code} not exists in {DistMatrix.table_name()}")
        if not self.location_manager.contains_location(dist_matrix.to_location_code):
            raise ValueError(f"Location {dist_matrix.to_location_code} not exists in {DistMatrix.table_name()}")

        self.net_work_manager.add_dist_matrix(dist_matrix)

    def add_carrier(self, carrier: Carrier):
        self.carrier_manager.add_carrier(carrier)

    def add_carrier_label_value(self, carrier_label_value: CarrierLabelValue):
        label_code = carrier_label_value.label_code
        if not self.label_manager.contains_label(label_code):
            raise ValueError(f"Label code {label_code} not exists in {CarrierLabelValue.table_name()}")

        label_value = carrier_label_value.label_value
        if not self.label_manager.contains_label_value(label_code, label_value):
            raise ValueError(f"Label code {label_code} label value {label_value} not exists "
                             f"in {CarrierLabelValue.table_name()}")

        if (not self.label_manager.item_label_map.__contains__(LabelApplyItem.CARRIER)
                or not self.label_manager.item_label_map[LabelApplyItem.CARRIER].__contains__(label_code)):
            raise ValueError(f"Label code {label_code} not support for carrier in {CarrierLabelValue.table_name()}")

        self.carrier_manager.add_carrier_label_value(carrier_label_value)

    def add_vehicle(self, vehicle: Vehicle):
        if not self.vehicle_model_manager.contains_vehicle_model(vehicle.vehicle_model_code):
            raise ValueError(f"Vehicle model code {vehicle.vehicle_model_code} not exists in {Vehicle.table_name()}")

        origin_location_code = vehicle.origin_location_code
        if (origin_location_code is not None
                and self.location_manager.contains_location(origin_location_code)):
            raise ValueError(f"Origin location code {origin_location_code} not exists "
                             f"in {Vehicle.table_name()}")

        destination_location_code = vehicle.destination_location_code
        if (destination_location_code is not None
                and self.location_manager.contains_location(destination_location_code)):
            raise ValueError(f"Destination location code {destination_location_code} not exists "
                             f"in {Vehicle.table_name()}")

        self.carrier_manager.add_vehicle(vehicle)

    def add_cargo_order(self, cargo_order: CargoOrder):
        if not self.location_manager.contains_location(cargo_order.pick_location_code):
            raise ValueError(f"Pick location code {cargo_order.pick_location_code} not exists "
                             f"for cargo order code {cargo_order.code} "
                             f"in {CargoOrder.table_name()}")

        if not self.location_manager.contains_location(cargo_order.drop_location_code):
            raise ValueError(f"Drop location code {cargo_order.drop_location_code} "
                             f"for cargo order code {cargo_order.code} "
                             f"in {CargoOrder.table_name()}")

        self.cargo_order_manager.add_cargo_order(cargo_order)

    def add_cargo_sub_order(self, cargo_sub_order: CargoSubOrder):
        self.cargo_order_manager.add_cargo_sub_order(cargo_sub_order)

    def add_cargo_sub_order_dimension_value(self, cargo_sub_order_dimension_value: CargoSubOrderDimensionValue):
        dimension_code = cargo_sub_order_dimension_value.dimension_code
        if not self.dimension_manager.contains_dimension(dimension_code):
            raise ValueError(f"Dimension code {dimension_code} not exists "
                             f"in {CargoSubOrderDimensionValue.table_name()}")
        self.cargo_order_manager.add_cargo_sub_order_dimension_value(cargo_sub_order_dimension_value)

    def add_cargo_sub_order_label_value(self, cargo_sub_order_label_value: CargoSubOrderLabelValue):
        label_code = cargo_sub_order_label_value.label_code
        if not self.label_manager.contains_label(label_code):
            raise ValueError(f"Label code {label_code} not exists in {CargoSubOrderLabelValue.table_name()}")

        label_value = cargo_sub_order_label_value.label_value
        if not self.label_manager.contains_label_value(label_code, label_value):
            raise ValueError(f"Label {label_code} label {label_value} not exists "
                             f"in {CargoSubOrderLabelValue.table_name()}")

        if (not self.label_manager.item_label_map.__contains__(LabelApplyItem.ORDER) or
                not self.label_manager.item_label_map[LabelApplyItem.ORDER].__contains__(label_code)):
            raise ValueError(f"Order label dose not support label code {label_code} "
                             f"in {CargoSubOrderLabelValue.table_name()}")

        self.cargo_order_manager.add_cargo_sub_order_label_value(cargo_sub_order_label_value)

    def to_csv(self, root_path: str):
        self.dimension_manager.to_csv(root_path)
        self.label_manager.to_csv(root_path)
        self.location_manager.to_csv(root_path)
        self.vehicle_model_manager.to_csv(root_path)
        self.carrier_manager.to_csv(root_path)
        self.net_work_manager.to_csv(root_path)
        self.cargo_order_manager.to_csv(root_path)
