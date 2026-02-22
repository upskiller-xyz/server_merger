"""Processing components and pipelines"""

from src.components.processing.context import (
    WindowInputData,
    ImagePair,
    PositionData,
    CropData,
    WindowProcessingContext,
)
from src.components.processing.pipeline import WindowProcessingPipeline
from src.components.processing.window_processor import WindowProcessor
from src.components.processing.window_aggregation_orchestrator import WindowAggregationOrchestrator

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
