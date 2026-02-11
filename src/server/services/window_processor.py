"""
Window Processing Utilities

This module provides the WindowProcessor class for processing individual window simulations.
"""

from typing import Tuple, Callable
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

    def __init__(self, logger: logging.Logger):
        """
        Initialize window processor.

        Args:
            logger: Logger instance
        """
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

        def resize_transform(img: np.ndarray) -> np.ndarray:
            return cv2.resize(
                img,
                (GRAPHICS_CONSTANTS.BASE_IMAGE_SIZE_PX, GRAPHICS_CONSTANTS.BASE_IMAGE_SIZE_PX),
                interpolation=cv2.INTER_NEAREST
            )

        return self._apply_transformation(df_values, mask, resize_transform)

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
        self.logger.info(f"  Rotating by {direction_angle:.4f} rad ({angle_deg:.2f}deg)")

        center = (
            df_values.shape[1] * 0.5,
            df_values.shape[0] * 0.5
        )

        rotation_matrix = self.rotation_helper.get_rotation_matrix(angle_deg, center)

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

        ref_rotated = self.rotation_helper.rotate_point(window_ref_px, rotation_matrix)

        self.logger.debug(f"  Reference point: {window_ref_px} -> {ref_rotated}")

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
        nonzero_coords = np.nonzero(mask)

        if len(nonzero_coords[0]) == 0:
            self.logger.warning(f"  No visible pixels found in mask for '{window_id}'")
            return df_values, mask, (AggregationConstants.ZERO_VALUE, AggregationConstants.ZERO_VALUE)

        y_min = np.min(nonzero_coords[0])
        y_max = np.max(nonzero_coords[0])
        x_min = np.min(nonzero_coords[1])
        x_max = np.max(nonzero_coords[1])

        df_cropped = df_values[y_min:y_max + 1, x_min:x_max + 1]
        mask_cropped = mask[y_min:y_max + 1, x_min:x_max + 1]
        crop_offset = (x_min, y_min)

        self.logger.info(
            f"  Cropped '{window_id}' from {df_values.shape} to {df_cropped.shape}, "
            f"offset: {crop_offset}"
        )

        return df_cropped, mask_cropped, crop_offset
