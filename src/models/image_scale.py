"""Image scale configuration model"""

from dataclasses import dataclass

from src.core.graphics_constants import GRAPHICS_CONSTANTS


@dataclass
class ImageScale:
    """
    Image scale configuration calculated proportionally from reference scale.
    Reference: 128x128 image with 0.1 m/px, window_offset = 12px
    """
    size: int
    meters_per_pixel: float

    @property
    def window_offset(self) -> int:
        """Calculate window offset proportionally from reference (12px at 128px)."""
        scale_factor = self.size / GRAPHICS_CONSTANTS.BASE_IMAGE_SIZE_PX
        return int(GRAPHICS_CONSTANTS.WINDOW_OFFSET_PX * scale_factor)

    @classmethod
    def from_image_size(cls, img_size: int) -> 'ImageScale':
        """
        Calculate scale proportionally based on reference (128px = 0.1m/px).

        Args:
            img_size: Size of the square image

        Returns:
            ImageScale instance with calculated meters_per_pixel
        """
        # Reference scale: 128px = 0.1 m/px
        scale_factor = img_size / GRAPHICS_CONSTANTS.BASE_IMAGE_SIZE_PX
        meters_per_pixel = GRAPHICS_CONSTANTS.BASE_RESOLUTION_M_PER_PX * scale_factor

        return cls(size=img_size, meters_per_pixel=meters_per_pixel)
