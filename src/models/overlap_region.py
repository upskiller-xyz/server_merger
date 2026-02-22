"""Overlap region model"""

from dataclasses import dataclass


@dataclass
class OverlapRegion:
    """Defines source and destination regions for overlap calculations"""
    src_y_start: int
    src_y_end: int
    src_x_start: int
    src_x_end: int
    dst_y_start: int
    dst_y_end: int
    dst_x_start: int
    dst_x_end: int

    @property
    def src_height(self) -> int:
        """Source region height"""
        return self.src_y_end - self.src_y_start

    @property
    def src_width(self) -> int:
        """Source region width"""
        return self.src_x_end - self.src_x_start

    @property
    def dst_height(self) -> int:
        """Destination region height"""
        return self.dst_y_end - self.dst_y_start

    @property
    def dst_width(self) -> int:
        """Destination region width"""
        return self.dst_x_end - self.dst_x_start
