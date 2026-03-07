"""Overlap region model"""

from dataclasses import dataclass


@dataclass
class Region:
    """Defines a rectangular region with bounds"""
    y_start: int
    y_end: int
    x_start: int
    x_end: int

    @property
    def height(self) -> int:
        """Region height"""
        return self.y_end - self.y_start

    @property
    def width(self) -> int:
        """Region width"""
        return self.x_end - self.x_start


@dataclass
class OverlapRegion:
    """Defines source and destination regions for overlap calculations"""
    src: Region
    dest: Region

    @property
    def src_height(self) -> int:
        """Source region height"""
        return self.src.height

    @property
    def src_width(self) -> int:
        """Source region width"""
        return self.src.width

    @property
    def dst_height(self) -> int:
        """Destination region height"""
        return self.dest.height

    @property
    def dst_width(self) -> int:
        """Destination region width"""
        return self.dest.width

    # Backward compatibility properties
    @property
    def src_y_start(self) -> int:
        """Source region y start"""
        return self.src.y_start

    @property
    def src_y_end(self) -> int:
        """Source region y end"""
        return self.src.y_end

    @property
    def src_x_start(self) -> int:
        """Source region x start"""
        return self.src.x_start

    @property
    def src_x_end(self) -> int:
        """Source region x end"""
        return self.src.x_end

    @property
    def dst_y_start(self) -> int:
        """Destination region y start"""
        return self.dest.y_start

    @property
    def dst_y_end(self) -> int:
        """Destination region y end"""
        return self.dest.y_end

    @property
    def dst_x_start(self) -> int:
        """Destination region x start"""
        return self.dest.x_start

    @property
    def dst_x_end(self) -> int:
        """Destination region x end"""
        return self.dest.x_end
