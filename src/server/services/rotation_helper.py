"""
Rotation Helper Utilities

This module provides helper functions for rotation operations.
"""

from typing import Tuple
import cv2
import numpy as np

from src.components.enums import AggregationConstants


class RotationHelper:
    """Helper class for rotation operations."""

    @staticmethod
    def get_rotation_matrix(angle_deg: float, center: Tuple[float, float]) -> np.ndarray:
        """
        Get rotation matrix for given angle and center.

        Args:
            angle_deg: Rotation angle in degrees
            center: Center point (x, y)

        Returns:
            2x3 rotation matrix
        """
        return cv2.getRotationMatrix2D(center, angle_deg, AggregationConstants.ROTATION_SCALE)

    @staticmethod
    def rotate_point(
        point: Tuple[int, int],
        rotation_matrix: np.ndarray
    ) -> Tuple[int, int]:
        """
        Rotate a point using rotation matrix.

        Args:
            point: Point coordinates (x, y)
            rotation_matrix: 2x3 rotation matrix

        Returns:
            Rotated point (x, y)
        """
        ref_x, ref_y = point
        ref_point_homogeneous = np.array([ref_x, ref_y, AggregationConstants.ROTATION_SCALE])
        ref_rotated_xy = rotation_matrix @ ref_point_homogeneous
        return (int(round(ref_rotated_xy[0])), int(round(ref_rotated_xy[1])))

    @staticmethod
    def rotate_image(
        image: np.ndarray,
        rotation_matrix: np.ndarray,
        output_size: Tuple[int, int]
    ) -> np.ndarray:
        """
        Rotate image using rotation matrix.

        Args:
            image: Input image
            rotation_matrix: 2x3 rotation matrix
            output_size: Output size (width, height)

        Returns:
            Rotated image
        """
        return cv2.warpAffine(
            image,
            rotation_matrix,
            output_size,
            flags=cv2.INTER_NEAREST,
            borderMode=cv2.BORDER_CONSTANT,
            borderValue=AggregationConstants.ZERO_VALUE
        )
