"""
Processing Steps for Window Transformation Pipeline

This module implements the Chain of Responsibility and Pipeline patterns
for window image processing. Each step is a separate class that operates
on a shared context object.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Tuple, Optional
from pathlib import Path
import numpy as np
import logging
import cv2
import os

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

    def __init__(self, logger: logging.Logger, debug_dir: Optional[Path] = None):
        """
        Initialize step with logger.

        Args:
            logger: Logger instance for step logging
            debug_dir: Optional debug directory for saving intermediate images
        """
        self.logger = logger
        self.debug_dir = debug_dir

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

    def _save_debug_image(self, img: np.ndarray, window_id: str, step_name: str, image_type: str) -> None:
        """
        Save debug image for intermediate processing steps.
        Only saves if DEBUG_SAVE_STEPS environment variable is set to 'true' or '1'.

        Args:
            img: Image array to save
            window_id: Window identifier
            step_name: Name of the processing step
            image_type: Type of image (df or mask)
        """
        # Check if debug saving is enabled via environment variable
        debug_enabled = os.getenv('DEBUG_SAVE_STEPS', '').lower() in ('true', '1', 'yes')

        if not debug_enabled or self.debug_dir is None:
            return

        try:
            filename = f"{window_id}_{step_name}_{image_type}.png"
            output_path = self.debug_dir / filename

            # Normalize to 0-255 range for visualization
            if img.max() > 0:
                img_normalized = (img / img.max() * 255).astype(np.uint8)
            else:
                img_normalized = img.astype(np.uint8)

            cv2.imwrite(str(output_path), img_normalized)
            self.logger.debug(f"  [DEBUG] Saved {step_name} {image_type}: {output_path}")
        except Exception as e:
            self.logger.warning(f"  Failed to save debug image {filename}: {e}")


class CalculateWindowPositionStep(ProcessingStep):
    """Calculate window position in room coordinates (meters and pixels)"""

    def __init__(self, scale_converter: ScaleConverter, logger: logging.Logger, debug_dir: Optional[Path] = None):
        super().__init__(logger, debug_dir)
        self.scale_converter = scale_converter

    def run(self, context: WindowProcessingContext) -> WindowProcessingContext:
        """Calculate window room coordinates and reference point"""
        self.logger.debug(f"Step 1: Calculating window position for '{context.input.window_id}'")

        # Get window reference point on room polygon (edge midpoint on room wall)
        # This gives us where the window facade touches the room
        room_coord_meters = context.input.window.reference_from_polygon(context.input.room_polygon)

        # Convert to room canvas coordinates
        # Use point_to_zero which handles the coordinate transformation correctly
        point_shifted = context.input.room_polygon.point_to_zero(room_coord_meters)
        # Validate shifted point
        if point_shifted.x is None or point_shifted.y is None:
            raise ValueError(
                f"Window {context.input.window_id}: point calculation returned None coordinates: "
                f"x={point_shifted.x}, y={point_shifted.y}"
            )

        room_coord_pixels = self.scale_converter.point_meters_to_pixels(point_shifted)
        # Validate converted pixels
        if room_coord_pixels.x is None or room_coord_pixels.y is None:
            raise ValueError(
                f"Window {context.input.window_id}: point_meters_to_pixels returned None coordinates: "
                f"x={room_coord_pixels.x}, y={room_coord_pixels.y}"
            )

        # Get window reference point in 128x128 image
        ref_px_original = context.input.window.get_reference_pixel()
        # Store position data
        context.position = PositionData(
            room_coord_meters=room_coord_meters,
            room_coord_pixels=room_coord_pixels,
            ref_px_original=ref_px_original
        )

        # TODO: TEMPORARY - Save original images (will be removed after debugging)
        self._save_debug_image(context.original_images.df_values, context.input.window_id, "01_original", "df")
        self._save_debug_image(context.original_images.mask, context.input.window_id, "01_original", "mask")

        return context


class StandardizeWindowStep(ProcessingStep):
    """Standardize window images to 128x128 at 0.1m/px"""

    def __init__(self, window_processor: WindowProcessor, logger: logging.Logger, debug_dir: Optional[Path] = None):
        super().__init__(logger, debug_dir)
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

        # TODO: TEMPORARY - Save standardized images (will be removed after debugging)
        self._save_debug_image(context.original_images.df_values, context.input.window_id, "02_standardized", "df")
        self._save_debug_image(context.original_images.mask, context.input.window_id, "02_standardized", "mask")

        return context


class RotateWindowStep(ProcessingStep):
    """Rotate window images and reference point by direction angle"""

    def __init__(self, window_processor: WindowProcessor, logger: logging.Logger, debug_dir: Optional[Path] = None):
        super().__init__(logger, debug_dir)
        self.window_processor = window_processor

    def run(self, context: WindowProcessingContext) -> WindowProcessingContext:
        """Apply rotation transformation"""
        self.logger.debug(f"Step 3: Rotating window '{context.input.window_id}'")

        # Reverse the encoder's rotation: encoder rotated by -direction_angle to align
        # window normal with +X, so we rotate by +direction_angle to restore original orientation
        rotation_angle = context.input.window.direction_angle if context.input.window.direction_angle is not None else 0

        df_rotated, mask_rotated, ref_px_rotated = (
            self.window_processor.rotate_window_images(
                context.original_images.df_values,
                context.original_images.mask,
                context.position.ref_px_original,
                rotation_angle,
                context.input.window_id
            )
        )

        context.original_images = ImagePair(df_rotated, mask_rotated)
        context.position.ref_px_rotated = ref_px_rotated

        # TODO: TEMPORARY - Save rotated images (will be removed after debugging)
        self._save_debug_image(context.original_images.df_values, context.input.window_id, "03_rotated", "df")
        self._save_debug_image(context.original_images.mask, context.input.window_id, "03_rotated", "mask")

        return context


class CropWindowStep(ProcessingStep):
    """Crop window images to visible (non-zero mask) bounds"""

    def __init__(self, window_processor: WindowProcessor, logger: logging.Logger, debug_dir: Optional[Path] = None):
        super().__init__(logger, debug_dir)
        self.window_processor = window_processor

    def run(self, context: WindowProcessingContext) -> WindowProcessingContext:
        """Crop to mask bounds"""

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

        # TODO: TEMPORARY - Save cropped images (will be removed after debugging)
        self._save_debug_image(context.original_images.df_values, context.input.window_id, "04_cropped", "df")
        self._save_debug_image(context.original_images.mask, context.input.window_id, "04_cropped", "mask")

        return context


class CalculateTranslationStep(ProcessingStep):
    """Calculate final translation offset for placing window on room canvas"""

    def __init__(self, logger: logging.Logger, debug_dir: Optional[Path] = None):
        super().__init__(logger, debug_dir)

    def run(self, context: WindowProcessingContext) -> WindowProcessingContext:
        """Calculate translation vector"""
        self.logger.debug(f"Step 5: Calculating translation for '{context.input.window_id}'")

        # Validate all components before calculation
        if context.position.room_coord_pixels.x is None or context.position.room_coord_pixels.y is None:
            raise ValueError(
                f"Room coordinates contain None: x={context.position.room_coord_pixels.x}, "
                f"y={context.position.room_coord_pixels.y}"
            )

        if context.position.ref_px_rotated is None or None in context.position.ref_px_rotated:
            raise ValueError(f"Rotated reference point is None or contains None: {context.position.ref_px_rotated}")

        if context.cropped.offset is None or None in context.cropped.offset:
            raise ValueError(f"Crop offset is None or contains None: {context.cropped.offset}")


        
        ref_x_in_crop = self._get_crop(context, axis=0)
        ref_y_in_crop = self._get_crop(context, axis=1)



        self.logger.debug("context position {}, {}".format(context.position.room_coord_pixels.x, context.position.room_coord_pixels.y))

        
        context.translation = Point2D(
            ref_x_in_crop,
            ref_y_in_crop
        )

        self.logger.debug(f"  Translation: {context.translation}")
        

        return context
    
    def _get_crop(self, context:WindowProcessingContext, axis:int)->int:
        pt = context.position.room_coord_pixels.x
        
        if axis == 1:
            pt = context.position.room_coord_pixels.y
        _crop = pt
        if context.position.ref_px_rotated[axis] > 105:
            _crop = context.position.ref_px_rotated[axis] - pt

        if context.position.ref_px_rotated[axis] ==64:
            _crop = 64 - pt
            
        return _crop


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
        # Pass window_processor.debug_dir to enable debug image saving
        debug_dir = window_processor.debug_dir if hasattr(window_processor, 'debug_dir') else None
        self.steps = [
            CalculateWindowPositionStep(scale_converter, logger, debug_dir),
            StandardizeWindowStep(window_processor, logger, debug_dir),
            RotateWindowStep(window_processor, logger, debug_dir),
            CropWindowStep(window_processor, logger, debug_dir),
            CalculateTranslationStep(logger, debug_dir)
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
