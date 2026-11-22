"""Processing components and pipelines"""

from src.components.processing.context import (
    CropData,
    ImagePair,
    PositionData,
    WindowInputData,
    WindowProcessingContext,
)
from src.components.processing.pipeline import WindowProcessingPipeline
from src.components.processing.window_aggregation_orchestrator import (
    WindowAggregationOrchestrator,
)
from src.components.processing.window_processor import WindowProcessor

__all__ = [
    "WindowInputData",
    "ImagePair",
    "PositionData",
    "CropData",
    "WindowProcessingContext",
    "WindowProcessingPipeline",
    "WindowProcessor",
    "WindowAggregationOrchestrator",
]
