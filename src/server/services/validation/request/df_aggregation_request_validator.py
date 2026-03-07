"""Validator for complete DF aggregation request"""

from typing import Dict, Any

from ..validation_error import ValidationError
from ..enums import ErrorCode
from .room_polygon_validator import RoomPolygonValidator
from .window_geometry_validator import WindowGeometryValidator
from .simulation_data_validator import SimulationDataValidator
from .enums import RequestField


class DFAggregationRequestValidator:
    """
    Validates complete DF aggregation request.

    Follows Single Responsibility Principle by delegating to specific validators.
    """

    def __init__(self):
        self.room_validator = RoomPolygonValidator()
        self.window_validator = WindowGeometryValidator()
        self.simulation_validator = SimulationDataValidator()

    def validate(self, data: Dict[str, Any]) -> None:
        """
        Validate complete DF aggregation request.

        Args:
            data: Request payload

        Raises:
            ValidationError: If validation fails with detailed error information
        """
        # Check top-level required fields
        required_top_level = [field.value for field in RequestField]
        for field in required_top_level:
            if field not in data:
                raise ValidationError(
                    message=f"Missing required field: {field}",
                    error_code=ErrorCode.MISSING_FIELD,
                    field=field
                )

        # Validate room polygon
        room_field = RequestField.ROOM_POLYGON.value
        self.room_validator.validate(data[room_field], room_field)

        # Validate windows dict not empty
        windows_field = RequestField.WINDOWS.value
        if not data[windows_field]:
            raise ValidationError(
                message="Windows dictionary cannot be empty",
                error_code=ErrorCode.EMPTY_DATA,
                field=windows_field
            )

        # Validate each window
        for window_id, window_data in data[windows_field].items():
            if not isinstance(window_data, dict):
                raise ValidationError(
                    message=f"Window '{window_id}' data must be a dictionary, got {type(window_data).__name__}",
                    error_code=ErrorCode.INVALID_TYPE,
                    field=f"{windows_field}.{window_id}"
                )
            self.window_validator.validate(window_data, f"{windows_field}.{window_id}")

        # Validate simulations dict not empty
        simulation_field = RequestField.SIMULATION.value
        if not data[simulation_field]:
            raise ValidationError(
                message="Simulation dictionary cannot be empty",
                error_code=ErrorCode.EMPTY_DATA,
                field=simulation_field
            )

        # Validate each simulation
        for window_id, sim_data in data[simulation_field].items():
            if not isinstance(sim_data, dict):
                raise ValidationError(
                    message=f"Simulation '{window_id}' data must be a dictionary, got {type(sim_data).__name__}",
                    error_code=ErrorCode.INVALID_TYPE,
                    field=f"{simulation_field}.{window_id}"
                )
            self.simulation_validator.validate(sim_data, f"{simulation_field}.{window_id}")

        # Validate window IDs match between windows and simulations
        window_ids = set(data[windows_field].keys())
        simulation_ids = set(data[simulation_field].keys())

        if window_ids != simulation_ids:
            missing_in_simulation = window_ids - simulation_ids
            missing_in_windows = simulation_ids - window_ids

            if missing_in_simulation:
                raise ValidationError(
                    message=f"Windows defined but missing simulation data: {', '.join(missing_in_simulation)}",
                    error_code=ErrorCode.MISSING_FIELD,
                    field=simulation_field,
                    context={"missing_window_ids": list(missing_in_simulation)}
                )

            if missing_in_windows:
                raise ValidationError(
                    message=f"Simulation data provided but window not defined: {', '.join(missing_in_windows)}",
                    error_code=ErrorCode.MISSING_FIELD,
                    field=windows_field,
                    context={"missing_window_ids": list(missing_in_windows)}
                )
