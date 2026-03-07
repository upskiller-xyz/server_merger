"""API request/response models using Pydantic for type safety and validation in Flask"""

from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field, ConfigDict

from src.server.services.validation.request.enums import (
    WindowField,
    SimulationField,
    RequestField,
    ResponseField
)


class WindowGeometry(BaseModel):
    """Window geometry definition"""
    model_config = ConfigDict(use_enum_values=True)

    x1: float = Field(..., alias=WindowField.X1.value, description="Window corner 1 x-coordinate")
    y1: float = Field(..., alias=WindowField.Y1.value, description="Window corner 1 y-coordinate")
    z1: float = Field(..., alias=WindowField.Z1.value, description="Window corner 1 z-coordinate (height)")
    x2: float = Field(..., alias=WindowField.X2.value, description="Window corner 2 x-coordinate")
    y2: float = Field(..., alias=WindowField.Y2.value, description="Window corner 2 y-coordinate")
    z2: float = Field(..., alias=WindowField.Z2.value, description="Window corner 2 z-coordinate (height)")
    direction_angle: float = Field(..., alias=WindowField.DIRECTION_ANGLE.value, description="Window direction angle in radians")


class SimulationData(BaseModel):
    """Simulation data for a single window"""
    model_config = ConfigDict(use_enum_values=True)

    df_values: List[List[float]] = Field(..., alias=SimulationField.DF_VALUES.value, description="Daylight factor values (2D array)")
    mask: List[List[int]] = Field(..., alias=SimulationField.MASK.value, description="Mask array (2D array)")


class MergeRequest(BaseModel):
    """
    DF aggregation/merge request model for type safety and validation.

    Can be used with endpoint_error_handler decorator for automatic validation.
    """
    model_config = ConfigDict(use_enum_values=True, json_schema_extra={
        "example": {
            RequestField.ROOM_POLYGON.value: [[0, 0], [10, 0], [10, 10], [0, 10]],
            RequestField.WINDOWS.value: {
                "window1": {
                    WindowField.X1.value: -0.6,
                    WindowField.Y1.value: 0.0,
                    WindowField.Z1.value: 1.0,
                    WindowField.X2.value: 0.6,
                    WindowField.Y2.value: 0.0,
                    WindowField.Z2.value: 2.5,
                    WindowField.DIRECTION_ANGLE.value: 0.0
                }
            },
            RequestField.SIMULATION.value: {
                "window1": {
                    SimulationField.DF_VALUES.value: [[]],
                    SimulationField.MASK.value: [[]]
                }
            }
        }
    })

    room_polygon: List[List[float]] = Field(
        ...,
        alias=RequestField.ROOM_POLYGON.value,
        description="Room polygon coordinates [[x1, y1], [x2, y2], ...]"
    )
    windows: Dict[str, WindowGeometry] = Field(
        ...,
        alias=RequestField.WINDOWS.value,
        description="Window geometries mapped by window ID"
    )
    simulation: Dict[str, SimulationData] = Field(
        ...,
        alias=RequestField.SIMULATION.value,
        description="Simulation data (df_values, mask) mapped by window ID"
    )


class MergeResponse(BaseModel):
    """
    DF aggregation/merge response model.
    """
    model_config = ConfigDict(use_enum_values=True, json_schema_extra={
        "example": {
            ResponseField.RESULT.value: [[]],
            ResponseField.MASK.value: [[]]
        }
    })

    result: List[List[float]] = Field(..., alias=ResponseField.RESULT.value, description="Aggregated DF matrix")
    mask: List[List[int]] = Field(..., alias=ResponseField.MASK.value, description="Room mask")


class ErrorResponse(BaseModel):
    """
    Standard error response model.
    """
    model_config = ConfigDict(use_enum_values=True, json_schema_extra={
        "example": {
            ResponseField.ERROR.value: "Missing required field: room_polygon",
            ResponseField.ERROR_CODE.value: "missing_field",
            ResponseField.FIELD.value: "room_polygon"
        }
    })

    error: str = Field(..., alias=ResponseField.ERROR.value, description="Error message")
    error_code: str = Field(default="error", alias=ResponseField.ERROR_CODE.value, description="Error code")
    field: Optional[str] = Field(default=None, alias=ResponseField.FIELD.value, description="Field that caused the error (if applicable)")
