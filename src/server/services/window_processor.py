"""
Window Processing Utilities

This module provides the WindowProcessor class for processing individual window simulations.
"""

from typing import Tuple, Callable
from pathlib import Path
import cv2
import numpy as np
import logging

from src.components.enums import AggregationConstants
from src.components.graphics_constants import GRAPHICS_CONSTANTS
from src.server.services.rotation_helper import RotationHelper


class WindowProcessor:
    """
    Processes individual window simulations.
    Handles standardization, rotation, and cropping.
    """

    def __init__(self, debug_dir: Path, logger: logging.Logger):
        """
        Initialize window processor.

        Args:
            debug_dir: Directory for debug images
            logger: Logger instance
        """
        self.debug_dir = debug_dir
        self.logger = logger
        self.rotation_helper = RotationHelper()

    def _apply_transformation(
        self,
        df_values: np.ndarray,
        mask: np.ndarray,
        transform_fn: Callable[[np.ndarray], np.ndarray],
        mask_transform_fn: Callable[[np.ndarray], np.ndarray] = None
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Apply the same transformation to both DF values and mask.

        Args:
            df_values: DF values array
            mask: Mask array
            transform_fn: Transformation function to apply to DF values
            mask_transform_fn: Optional separate transformation for mask (uses transform_fn if None)

        Returns:
            (transformed_df, transformed_mask)
        """
        df_transformed = transform_fn(df_values)
        mask_transformed = (mask_transform_fn or transform_fn)(mask)
        return df_transformed, mask_transformed

    def standardize_window_images(
        self,
        df_values: np.ndarray,
        mask: np.ndarray,
        window_id: str
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Standardize window images to 128x128 at 0.1m/px scale.

        Args:
            df_values: Input DF values array
            mask: Input mask array
            window_id: Window identifier for logging

        Returns:
            (df_standardized, mask_standardized): Both at 128x128 resolution
        """
        current_size = df_values.shape[0]

        self.logger.debug(
            f"  Input DF shape: {df_values.shape}, "
            f"range: [{df_values.min():.4f}, {df_values.max():.4f}]"
        )
        self.logger.debug(
            f"  Input mask shape: {mask.shape}, unique values: {np.unique(mask)}"
        )

        if current_size == GRAPHICS_CONSTANTS.BASE_IMAGE_SIZE_PX:
            self.logger.debug(
                f"  Already at standard size "
                f"{GRAPHICS_CONSTANTS.BASE_IMAGE_SIZE_PX}x{GRAPHICS_CONSTANTS.BASE_IMAGE_SIZE_PX}, "
                f"skipping resize"
            )
            return df_values.copy(), mask.copy()

        self.logger.info(
            f"  Resizing from {current_size}x{current_size} to "
            f"{GRAPHICS_CONSTANTS.BASE_IMAGE_SIZE_PX}x{GRAPHICS_CONSTANTS.BASE_IMAGE_SIZE_PX}"
        )

        # Define resize transformation
        def resize_transform(img: np.ndarray) -> np.ndarray:
            return cv2.resize(
                img,
                (GRAPHICS_CONSTANTS.BASE_IMAGE_SIZE_PX, GRAPHICS_CONSTANTS.BASE_IMAGE_SIZE_PX),
                interpolation=cv2.INTER_NEAREST
            )

        df_std, mask_std = self._apply_transformation(df_values, mask, resize_transform)

        self.logger.debug(f"  After resize - DF range: [{df_std.min():.4f}, {df_std.max():.4f}]")
        self.logger.debug(f"  After resize - Mask unique: {np.unique(mask_std)}")

        return df_std, mask_std

    def rotate_window_images(
        self,
        df_values: np.ndarray,
        mask: np.ndarray,
        window_ref_px: Tuple[int, int],
        direction_angle: float,
        window_id: str
    ) -> Tuple[np.ndarray, np.ndarray, Tuple[int, int]]:
        """
        Rotate window images by direction_angle and rotate the reference point.

        Args:
            df_values: Standardized DF values (128x128)
            mask: Standardized mask (128x128)
            window_ref_px: Reference point in original image (x, y)
            direction_angle: Rotation angle in radians
            window_id: Window identifier for logging

        Returns:
            (df_rotated, mask_rotated, ref_rotated): Rotated images and rotated reference point
        """
        angle_deg = np.degrees(direction_angle)
        self.logger.info(f"  Rotating by {direction_angle:.4f} rad ({angle_deg:.2f}°)")

        center = (
            df_values.shape[1] * 0.5,
            df_values.shape[0] * 0.5
        )

        rotation_matrix = self.rotation_helper.get_rotation_matrix(angle_deg, center)
        self.logger.debug(f"  Rotation center: {center}")

        # Define rotation transformations
        def rotate_df_transform(img: np.ndarray) -> np.ndarray:
            return self.rotation_helper.rotate_image(
                img, rotation_matrix, (img.shape[1], img.shape[0])
            )

        def rotate_mask_transform(img: np.ndarray) -> np.ndarray:
            return self.rotation_helper.rotate_image(
                img.astype(np.uint8), rotation_matrix, (img.shape[1], img.shape[0])
            )

        df_rotated, mask_rotated = self._apply_transformation(
            df_values, mask, rotate_df_transform, rotate_mask_transform
        )
        # Rotate the reference point
        ref_rotated = self.rotation_helper.rotate_point(window_ref_px, rotation_matrix)

        self.logger.debug(
            f"  After rotation - DF range: [{df_rotated.min():.4f}, {df_rotated.max():.4f}]"
        )
        self.logger.debug(f"  After rotation - Mask unique: {np.unique(mask_rotated)}")
        self.logger.debug(
            f"  After rotation - Non-zero mask pixels: {np.count_nonzero(mask_rotated)}"
        )
        self.logger.debug(f"  After rotation - Reference point: {window_ref_px} → {ref_rotated}")

        return df_rotated, mask_rotated, ref_rotated

    def crop_to_visible_bounds(
        self,
        df_values: np.ndarray,
        mask: np.ndarray,
        window_id: str
    ) -> Tuple[np.ndarray, np.ndarray, Tuple[int, int]]:
        """
        Crop DF and mask to the visible (non-zero mask) bounds.

        Args:
            df_values: Rotated DF values
            mask: Rotated mask
            window_id: Window identifier for logging

        Returns:
            (df_cropped, mask_cropped, crop_offset):
                - df_cropped: Cropped DF values
                - mask_cropped: Cropped mask
                - crop_offset: (offset_x, offset_y) of crop region in original image
        """
        # TEMPORARY FIX: Disable cropping to avoid reference point alignment issues
        # The issue is that mask bounds may not include the window reference point (row 64)
        # which causes incorrect placement. Cropping is just an optimization anyway.
        self.logger.info(f"  Skipping crop (keeping full {df_values.shape} image)")
        return df_values, mask, (AggregationConstants.ZERO_VALUE, AggregationConstants.ZERO_VALUE)

    def _save_debug_image(self, img: np.ndarray, filename: str) -> None:
        """
        Save debug image to tmp folder.

        Args:
            img: Image array (will be normalized to 0-255 for saving)
            filename: Output filename
        """
        try:
            output_path = self.debug_dir / filename

            # Normalize to 0-255 range for visualization
            if img.max() > AggregationConstants.ZERO_VALUE:
                img_normalized = (img / img.max() * AggregationConstants.GRAYSCALE_MAX).astype(np.uint8)
            else:
                img_normalized = img.astype(np.uint8)

            cv2.imwrite(str(output_path), img_normalized)
            self.logger.debug(f"  Saved debug image: {output_path}")
        except Exception as e:
            self.logger.warning(f"  Failed to save debug image {filename}: {e}")
