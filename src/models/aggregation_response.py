"""Data model for aggregation response."""

from typing import List


class AggregationResponse:
    """Response model for daylight factor aggregation results."""

    def __init__(self, result: List[List[float]], mask: List[List[int]]):
        """
        Initialize aggregation response.

        Args:
            result: 2D list containing aggregated daylight factor matrix
            mask: 2D list containing room mask (1 for inside room, 0 for outside)
        """
        self.result = result
        self.mask = mask

    def to_dict(self) -> dict:
        """
        Convert to dictionary format.

        Returns:
            Dictionary with 'result' and 'mask' keys
        """
        return {
            'result': self.result,
            'mask': self.mask
        }

    @classmethod
    def from_arrays(cls, df_matrix, room_mask) -> 'AggregationResponse':
        """
        Create AggregationResponse from numpy arrays.

        Args:
            df_matrix: Numpy array containing daylight factor values
            room_mask: Numpy array containing room mask

        Returns:
            AggregationResponse instance
        """
        return cls(
            result=df_matrix.tolist(),
            mask=room_mask.tolist()
        )
