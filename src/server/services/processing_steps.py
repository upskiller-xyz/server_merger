"""
Processing Steps for Window Transformation Pipeline

This module implements the Chain of Responsibility and Pipeline patterns
for window image processing. Each step is a separate class that operates
on a shared context object.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Tuple, Optional
import numpy as np
import logging

from src.components.geometry_ops import Point2D
from src.components.window import WindowGeometry, RoomPolygon
from src.server.services.window_processor import WindowProcessor
from src.server.services.scale_converter import ScaleConverter


@dataclass
class WindowInputData:
    """Immutable input data for window processing"""
    window_id: str
    window: WindowGeometry
    room_polygon: RoomPolygon


@dataclass
class ImagePair:
    """Pair of DF values and mask arrays at a processing stage"""
    df_values: np.ndarray
    mask: np.ndarray


@dataclass
class PositionData:
    """Window position information in room coordinates"""
    room_coord_meters: Point2D
    room_coord_pixels: Point2D
    ref_px_original: Tuple[int, int]
    ref_px_rotated: Optional[Tuple[int, int]] = None


@dataclass
class CropData:
    """Cropped image data with offset information"""
    images: ImagePair
    offset: Tuple[int, int]


@dataclass
class WindowProcessingContext:
    """
    Context object that passes through the processing pipeline.

    Groups related data semantically for better organization.
    """
    # Input data (immutable)
    input: WindowInputData
    original_images: ImagePair

    # Processing state (populated by steps)
    position: Optional[PositionData] = None
    # standardized: Optional[ImagePair] = None
    # rotated: Optional[ImagePair] = None
    cropped: Optional[CropData] = None
    translation: Optional[Point2D] = None


class ProcessingStep(ABC):
    """
    Abstract base class for processing steps.

    Each step implements the run() method which operates on the context.
    """

    def __init__(self, logger: logging.Logger):
        """
        Initialize step with logger.

        Args:
            logger: Logger instance for step logging
        """
        self.logger = logger

    @abstractmethod
    def run(self, context: WindowProcessingContext) -> WindowProcessingContext:
        """
        Execute this processing step.

        Args:
            context: Current processing context

        Returns:
            Updated context with this step's results
        """
        pass


class CalculateWindowPositionStep(ProcessingStep):
    """Calculate window position in room coordinates (meters and pixels)"""

    def __init__(self, scale_converter: ScaleConverter, logger: logging.Logger):
        super().__init__(logger)
        self.scale_converter = scale_converter

    def run(self, context: WindowProcessingContext) -> WindowProcessingContext:
        """Calculate window room coordinates and reference point"""
        self.logger.debug(f"Step 1: Calculating window position for '{context.input.window_id}'")

        # Get window reference point on room polygon (meters)
        room_coord_meters = context.input.window.reference_from_polygon(context.input.room_polygon)

        # Convert to pixels
        room_coord_pixels = self.scale_converter.point_meters_to_pixels(
            context.input.room_polygon.point_to_zero(room_coord_meters)
        )

        # Get window reference point in 128x128 image
        ref_px_original = context.input.window.get_reference_pixel()

        # Store position data
        context.position = PositionData(
            room_coord_meters=room_coord_meters,
            room_coord_pixels=room_coord_pixels,
            ref_px_original=ref_px_original
        )

        self.logger.debug(f"  Window room coord: {context.position.room_coord_meters}")
        self.logger.debug(f"  Window room coord (px): {context.position.room_coord_pixels}")

        return context


class StandardizeWindowStep(ProcessingStep):
    """Standardize window images to 128x128 at 0.1m/px"""

    def __init__(self, window_processor: WindowProcessor, logger: logging.Logger):
        super().__init__(logger)
        self.window_processor = window_processor

    def run(self, context: WindowProcessingContext) -> WindowProcessingContext:
        """Resize images to standard 128x128 resolution"""
        self.logger.debug(f"Step 2: Standardizing window '{context.input.window_id}' to 128x128")

        df_std, mask_std = self.window_processor.standardize_window_images(
            context.original_images.df_values,
            context.original_images.mask,
            context.input.window_id
        )

        context.original_images = ImagePair(df_std, mask_std)

        return context


class RotateWindowStep(ProcessingStep):
    """Rotate window images and reference point by direction angle"""

    def __init__(self, window_processor: WindowProcessor, logger: logging.Logger):
        super().__init__(logger)
        self.window_processor = window_processor

    def run(self, context: WindowProcessingContext) -> WindowProcessingContext:
        """Apply rotation transformation"""
        self.logger.debug(f"Step 3: Rotating window '{context.input.window_id}'")

        df_rotated, mask_rotated, ref_px_rotated = (
            self.window_processor.rotate_window_images(
                context.original_images.df_values,
                context.original_images.mask,
                context.position.ref_px_original,
                -context.input.window.direction_angle,
                context.input.window_id
            )
        )

        context.original_images = ImagePair(df_rotated, mask_rotated)
        context.position.ref_px_rotated = ref_px_rotated
        

        return context


class CropWindowStep(ProcessingStep):
    """Crop window images to visible (non-zero mask) bounds"""

    def __init__(self, window_processor: WindowProcessor, logger: logging.Logger):
        super().__init__(logger)
        self.window_processor = window_processor

    def run(self, context: WindowProcessingContext) -> WindowProcessingContext:
        """Crop to mask bounds"""
        self.logger.debug(f"Step 4: Cropping window '{context.input.window_id}'")
        
        df_cropped, mask_cropped, crop_offset = (
            self.window_processor.crop_to_visible_bounds(
                context.original_images.df_values,
                context.original_images.mask,
                context.input.window_id
            )
        )
        context.original_images = ImagePair(df_cropped, mask_cropped)
        context.cropped = CropData(
            images=ImagePair(df_cropped, mask_cropped),
            offset=crop_offset
        )
        return context


class CalculateTranslationStep(ProcessingStep):
    """Calculate final translation offset for placing window on room canvas"""

    def __init__(self, logger: logging.Logger):
        super().__init__(logger)

    def run(self, context: WindowProcessingContext) -> WindowProcessingContext:
        """Calculate translation vector"""
        self.logger.debug(f"Step 5: Calculating translation for '{context.input.window_id}'")

        context.translation = Point2D(
            context.position.room_coord_pixels.x - context.position.ref_px_rotated[0] + context.cropped.offset[0],
            context.position.room_coord_pixels.y - context.position.ref_px_rotated[1] + context.cropped.offset[1]
        )

        self.logger.debug(f"  Translation: {context.translation}")

        return context


class WindowProcessingPipeline:
    """
    Pipeline that executes a sequence of processing steps.

    Implements the Pipeline pattern where each step operates on a shared context.
    """

    def __init__(
        self,
        window_processor: WindowProcessor,
        scale_converter: ScaleConverter,
        logger: logging.Logger
    ):
        """
        Initialize pipeline with dependencies.

        Args:
            window_processor: Window processor for transformations
            scale_converter: Scale converter for coordinate transformations
            logger: Logger instance
        """
        self.logger = logger

        # Create processing steps in order
        self.steps = [
            CalculateWindowPositionStep(scale_converter, logger),
            StandardizeWindowStep(window_processor, logger),
            RotateWindowStep(window_processor, logger),
            CropWindowStep(window_processor, logger),
            CalculateTranslationStep(logger)
        ]

    def process(
        self,
        window_id: str,
        window: WindowGeometry,
        df_values: np.ndarray,
        mask: np.ndarray,
        room_polygon: RoomPolygon
    ) -> WindowProcessingContext:
        """
        Process window through the pipeline.

        Args:
            window_id: Window identifier
            window: Window geometry
            df_values: Original DF values
            mask: Original mask
            room_polygon: Room polygon

        Returns:
            Completed context with all processing results
        """
        # Create initial context with new structure
        context = WindowProcessingContext(
            input=WindowInputData(window_id, window, room_polygon),
            original_images=ImagePair(df_values, mask)
        )
        # Execute each step in sequence
        for step in self.steps:
            context = step.run(context)

        return context
