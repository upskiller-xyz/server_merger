"""Validator for simulation data (df_values and mask)"""

from typing import Dict, Any
import numpy as np

from ..validation_error import ValidationError
from ..enums import ErrorCode
from ..base_validator import Validator
from .enums import SimulationField


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
        df_field = SimulationField.DF_VALUES.value
        mask_field = SimulationField.MASK.value

        # Check required fields
        if df_field not in value:
            raise ValidationError(
                message=f"Simulation data missing '{df_field}' field",
                error_code=ErrorCode.MISSING_FIELD,
                field=f"{field_path}.{df_field}"
            )

        if mask_field not in value:
            raise ValidationError(
                message=f"Simulation data missing '{mask_field}' field",
                error_code=ErrorCode.MISSING_FIELD,
                field=f"{field_path}.{mask_field}"
            )

        # Validate df_values
        df_values = value[df_field]
        if not isinstance(df_values, (list, np.ndarray)):
            raise ValidationError(
                message=f"Field '{df_field}' must be an array, got {type(df_values).__name__}",
                error_code=ErrorCode.INVALID_TYPE,
                field=f"{field_path}.{df_field}"
            )

        df_arr = np.array(df_values)

        # Check 2D
        if df_arr.ndim != 2:
            raise ValidationError(
                message=f"Field '{df_field}' must be 2D array, got {df_arr.ndim}D with shape {df_arr.shape}",
                error_code=ErrorCode.INVALID_DIMENSIONS,
                field=f"{field_path}.{df_field}",
                context={"shape": df_arr.shape}
            )

        # Check square
        if df_arr.shape[0] != df_arr.shape[1]:
            raise ValidationError(
                message=f"Field '{df_field}' must be square array, got shape {df_arr.shape}",
                error_code=ErrorCode.INVALID_DIMENSIONS,
                field=f"{field_path}.{df_field}",
                context={"shape": df_arr.shape}
            )

        # Check valid size
        if df_arr.shape[0] not in self.valid_sizes:
            raise ValidationError(
                message=f"Field '{df_field}' must be one of sizes {self.valid_sizes}x{self.valid_sizes}, got {df_arr.shape[0]}x{df_arr.shape[0]}",
                error_code=ErrorCode.INVALID_DIMENSIONS,
                field=f"{field_path}.{df_field}",
                context={"shape": df_arr.shape, "valid_sizes": self.valid_sizes}
            )

        # Validate mask
        mask = value[mask_field]
        if not isinstance(mask, (list, np.ndarray)):
            raise ValidationError(
                message=f"Field '{mask_field}' must be an array, got {type(mask).__name__}",
                error_code=ErrorCode.INVALID_TYPE,
                field=f"{field_path}.{mask_field}"
            )

        mask_arr = np.array(mask)

        # Check 2D
        if mask_arr.ndim != 2:
            raise ValidationError(
                message=f"Field '{mask_field}' must be 2D array, got {mask_arr.ndim}D with shape {mask_arr.shape}",
                error_code=ErrorCode.INVALID_DIMENSIONS,
                field=f"{field_path}.{mask_field}",
                context={"shape": mask_arr.shape}
            )

        # Warn if shapes don't match (will be resized but user should know)
        if df_arr.shape != mask_arr.shape:
            # This is a warning case, not an error (service will resize)
            # But we should inform the user
            pass  # Service logs this already
