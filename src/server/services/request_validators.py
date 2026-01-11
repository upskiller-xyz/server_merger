"""
Request-specific validators for different endpoints.

This module contains validation logic specific to each API endpoint.
"""

from typing import Dict, Any
import numpy as np

from src.server.services.validation import (
    ValidationError,
    ErrorCode,
    Validator,
    NonEmptyValidator,
    ArrayShapeValidator,
    TypeValidator,
    RangeValidator
)


class WindowGeometryValidator(Validator):
    """Validates window geometry parameters"""

    def validate(self, value: Dict[str, Any], field_path: str) -> None:
        """
        Validate window geometry has all required fields and valid values.

        Args:
            value: Window geometry dictionary
            field_path: Path to this window in request
        """
        required_fields = ["x1", "y1", "z1", "x2", "y2", "z2", "direction_angle"]

        # Check required fields
        for field in required_fields:
            if field not in value:
                raise ValidationError(
                    message=f"Window geometry missing required field: {field}",
                    error_code=ErrorCode.MISSING_FIELD,
                    field=f"{field_path}.{field}"
                )

            # Validate numeric type
            if not isinstance(value[field], (int, float, np.integer, np.floating)):
                raise ValidationError(
                    message=f"Window parameter '{field}' must be numeric, got {type(value[field]).__name__}",
                    error_code=ErrorCode.INVALID_TYPE,
                    field=f"{field_path}.{field}",
                    value=value[field]
                )

        # Validate z1 < z2 (height constraint)
        if value["z1"] >= value["z2"]:
            raise ValidationError(
                message=f"Window z1 ({value['z1']}) must be less than z2 ({value['z2']})",
                error_code=ErrorCode.INVALID_VALUE,
                field=f"{field_path}.z1",
                context={"z1": value["z1"], "z2": value["z2"]}
            )


class SimulationDataValidator(Validator):
    """Validates simulation data (df_values and mask)"""

    def __init__(self, valid_sizes: tuple = (128, 384)):
        self.valid_sizes = valid_sizes

    def validate(self, value: Dict[str, Any], field_path: str) -> None:
        """
        Validate simulation data has correct structure and dimensions.

        Args:
            value: Simulation data dictionary
            field_path: Path to this simulation in request
        """
        # Check required fields
        if "df_values" not in value:
            raise ValidationError(
                message="Simulation data missing 'df_values' field",
                error_code=ErrorCode.MISSING_FIELD,
                field=f"{field_path}.df_values"
            )

        if "mask" not in value:
            raise ValidationError(
                message="Simulation data missing 'mask' field",
                error_code=ErrorCode.MISSING_FIELD,
                field=f"{field_path}.mask"
            )

        # Validate df_values
        df_values = value["df_values"]
        if not isinstance(df_values, (list, np.ndarray)):
            raise ValidationError(
                message=f"Field 'df_values' must be an array, got {type(df_values).__name__}",
                error_code=ErrorCode.INVALID_TYPE,
                field=f"{field_path}.df_values"
            )

        df_arr = np.array(df_values)

        # Check 2D
        if df_arr.ndim != 2:
            raise ValidationError(
                message=f"Field 'df_values' must be 2D array, got {df_arr.ndim}D with shape {df_arr.shape}",
                error_code=ErrorCode.INVALID_DIMENSIONS,
                field=f"{field_path}.df_values",
                context={"shape": df_arr.shape}
            )

        # Check square
        if df_arr.shape[0] != df_arr.shape[1]:
            raise ValidationError(
                message=f"Field 'df_values' must be square array, got shape {df_arr.shape}",
                error_code=ErrorCode.INVALID_DIMENSIONS,
                field=f"{field_path}.df_values",
                context={"shape": df_arr.shape}
            )

        # Check valid size
        if df_arr.shape[0] not in self.valid_sizes:
            raise ValidationError(
                message=f"Field 'df_values' must be one of sizes {self.valid_sizes}x{self.valid_sizes}, got {df_arr.shape[0]}x{df_arr.shape[0]}",
                error_code=ErrorCode.INVALID_DIMENSIONS,
                field=f"{field_path}.df_values",
                context={"shape": df_arr.shape, "valid_sizes": self.valid_sizes}
            )

        # Validate mask
        mask = value["mask"]
        if not isinstance(mask, (list, np.ndarray)):
            raise ValidationError(
                message=f"Field 'mask' must be an array, got {type(mask).__name__}",
                error_code=ErrorCode.INVALID_TYPE,
                field=f"{field_path}.mask"
            )

        mask_arr = np.array(mask)

        # Check 2D
        if mask_arr.ndim != 2:
            raise ValidationError(
                message=f"Field 'mask' must be 2D array, got {mask_arr.ndim}D with shape {mask_arr.shape}",
                error_code=ErrorCode.INVALID_DIMENSIONS,
                field=f"{field_path}.mask",
                context={"shape": mask_arr.shape}
            )

        # Warn if shapes don't match (will be resized but user should know)
        if df_arr.shape != mask_arr.shape:
            # This is a warning case, not an error (service will resize)
            # But we should inform the user
            pass  # Service logs this already


class RoomPolygonValidator(Validator):
    """Validates room polygon structure"""

    def __init__(self, min_vertices: int = 3):
        self.min_vertices = min_vertices

    def validate(self, value: Any, field_path: str) -> None:
        """
        Validate room polygon is a valid 2D polygon.

        Args:
            value: Room polygon coordinates
            field_path: Path to polygon in request
        """
        if not isinstance(value, (list, np.ndarray)):
            raise ValidationError(
                message=f"Room polygon must be an array, got {type(value).__name__}",
                error_code=ErrorCode.INVALID_TYPE,
                field=field_path
            )

        polygon = np.array(value)

        # Check minimum vertices
        if len(polygon) < self.min_vertices:
            raise ValidationError(
                message=f"Room polygon must have at least {self.min_vertices} vertices, got {len(polygon)}",
                error_code=ErrorCode.INVALID_VALUE,
                field=field_path,
                context={"vertex_count": len(polygon), "min_vertices": self.min_vertices}
            )

        # Check each vertex is [x, y]
        for i, vertex in enumerate(polygon):
            try:
                vertex_arr = np.array(vertex)
            except (TypeError, ValueError) as e:
                raise ValidationError(
                    message=f"Room polygon vertex {i} is invalid: {e}",
                    error_code=ErrorCode.INVALID_VALUE,
                    field=f"{field_path}[{i}]",
                    value=str(vertex)
                )

            if not isinstance(vertex, (list, tuple, np.ndarray)) or len(vertex) != 2:
                raise ValidationError(
                    message=f"Room polygon vertex {i} must be [x, y] coordinate pair (2D), got {len(vertex)} dimensions",
                    error_code=ErrorCode.INVALID_VALUE,
                    field=f"{field_path}[{i}]",
                    value=str(vertex)
                )

            # Check both coordinates are numeric
            try:
                float(vertex[0])
                float(vertex[1])
            except (TypeError, ValueError):
                raise ValidationError(
                    message=f"Room polygon vertex {i} coordinates must be numeric, got {vertex}",
                    error_code=ErrorCode.INVALID_TYPE,
                    field=f"{field_path}[{i}]",
                    value=vertex
                )


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
        required_top_level = ["room_polygon", "windows", "simulation"]
        for field in required_top_level:
            if field not in data:
                raise ValidationError(
                    message=f"Missing required field: {field}",
                    error_code=ErrorCode.MISSING_FIELD,
                    field=field
                )

        # Validate room polygon
        self.room_validator.validate(data["room_polygon"], "room_polygon")

        # Validate windows dict not empty
        if not data["windows"]:
            raise ValidationError(
                message="Windows dictionary cannot be empty",
                error_code=ErrorCode.EMPTY_DATA,
                field="windows"
            )

        # Validate each window
        for window_id, window_data in data["windows"].items():
            if not isinstance(window_data, dict):
                raise ValidationError(
                    message=f"Window '{window_id}' data must be a dictionary, got {type(window_data).__name__}",
                    error_code=ErrorCode.INVALID_TYPE,
                    field=f"windows.{window_id}"
                )
            self.window_validator.validate(window_data, f"windows.{window_id}")

        # Validate simulations dict not empty
        if not data["simulation"]:
            raise ValidationError(
                message="Simulation dictionary cannot be empty",
                error_code=ErrorCode.EMPTY_DATA,
                field="simulation"
            )

        # Validate each simulation
        for window_id, sim_data in data["simulation"].items():
            if not isinstance(sim_data, dict):
                raise ValidationError(
                    message=f"Simulation '{window_id}' data must be a dictionary, got {type(sim_data).__name__}",
                    error_code=ErrorCode.INVALID_TYPE,
                    field=f"simulation.{window_id}"
                )
            self.simulation_validator.validate(sim_data, f"simulation.{window_id}")

        # Validate window IDs match between windows and simulations
        window_ids = set(data["windows"].keys())
        simulation_ids = set(data["simulation"].keys())

        if window_ids != simulation_ids:
            missing_in_simulation = window_ids - simulation_ids
            missing_in_windows = simulation_ids - window_ids

            if missing_in_simulation:
                raise ValidationError(
                    message=f"Windows defined but missing simulation data: {', '.join(missing_in_simulation)}",
                    error_code=ErrorCode.MISSING_FIELD,
                    field="simulation",
                    context={"missing_window_ids": list(missing_in_simulation)}
                )

            if missing_in_windows:
                raise ValidationError(
                    message=f"Simulation data provided but window not defined: {', '.join(missing_in_windows)}",
                    error_code=ErrorCode.MISSING_FIELD,
                    field="windows",
                    context={"missing_window_ids": list(missing_in_windows)}
                )
