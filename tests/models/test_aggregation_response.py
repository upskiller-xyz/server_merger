"""Tests for aggregation response model."""

import pytest
import numpy as np
from src.models.aggregation_response import AggregationResponse


class TestAggregationResponse:
    """Test AggregationResponse class."""

    def test_aggregation_response_creation(self):
        """Test creating AggregationResponse."""
        result = [[0.1, 0.2], [0.3, 0.4]]
        mask = [[1, 1], [1, 0]]
        response = AggregationResponse(result=result, mask=mask)
        
        assert response.result == result
        assert response.mask == mask

    def test_aggregation_response_to_dict(self):
        """Test converting to dictionary."""
        result = [[0.1, 0.2], [0.3, 0.4]]
        mask = [[1, 1], [1, 0]]
        response = AggregationResponse(result=result, mask=mask)
        
        result_dict = response.to_dict()
        assert isinstance(result_dict, dict)
        assert 'result' in result_dict
        assert 'mask' in result_dict
        assert result_dict['result'] == result
        assert result_dict['mask'] == mask

    def test_aggregation_response_from_arrays(self):
        """Test creating from numpy arrays."""
        df_matrix = np.array([[0.1, 0.2], [0.3, 0.4]], dtype=np.float32)
        room_mask = np.array([[1, 1], [1, 0]], dtype=np.uint8)
        
        response = AggregationResponse.from_arrays(df_matrix, room_mask)
        
        assert response.result == df_matrix.tolist()
        assert response.mask == room_mask.tolist()

    def test_aggregation_response_from_arrays_2d(self):
        """Test creating from 2D arrays."""
        df_matrix = np.random.rand(10, 10).astype(np.float32) * 0.5
        room_mask = np.ones((10, 10), dtype=np.uint8)
        room_mask[5:, :] = 0
        
        response = AggregationResponse.from_arrays(df_matrix, room_mask)
        
        assert len(response.result) == 10
        assert len(response.result[0]) == 10
        assert len(response.mask) == 10
        assert len(response.mask[0]) == 10

    def test_aggregation_response_large_array(self):
        """Test with large arrays."""
        df_matrix = np.random.rand(256, 256).astype(np.float32) * 0.5
        room_mask = np.ones((256, 256), dtype=np.uint8)
        
        response = AggregationResponse.from_arrays(df_matrix, room_mask)
        
        assert len(response.result) == 256
        assert len(response.result[0]) == 256

    def test_aggregation_response_zero_values(self):
        """Test with zero values."""
        result = [[0.0, 0.0], [0.0, 0.0]]
        mask = [[0, 0], [0, 0]]
        response = AggregationResponse(result=result, mask=mask)
        
        assert response.result == result
        assert response.mask == mask

    def test_aggregation_response_max_values(self):
        """Test with maximum values."""
        result = [[1.0, 1.0], [1.0, 1.0]]
        mask = [[1, 1], [1, 1]]
        response = AggregationResponse(result=result, mask=mask)
        
        assert response.result == result
        assert response.mask == mask

    def test_aggregation_response_mixed_values(self):
        """Test with mixed values."""
        result = [[0.0, 0.5, 1.0], [0.1, 0.6, 0.9]]
        mask = [[0, 1, 1], [1, 1, 0]]
        response = AggregationResponse(result=result, mask=mask)
        
        assert response.result == result
        assert response.mask == mask

    def test_aggregation_response_empty_result(self):
        """Test with empty result."""
        result = []
        mask = []
        response = AggregationResponse(result=result, mask=mask)
        
        assert response.result == []
        assert response.mask == []

    def test_aggregation_response_single_row(self):
        """Test with single row."""
        result = [[0.1, 0.2, 0.3, 0.4, 0.5]]
        mask = [[1, 1, 1, 1, 1]]
        response = AggregationResponse(result=result, mask=mask)
        
        assert len(response.result) == 1
        assert len(response.result[0]) == 5

    def test_aggregation_response_single_column(self):
        """Test with single column."""
        result = [[0.1], [0.2], [0.3], [0.4]]
        mask = [[1], [1], [1], [0]]
        response = AggregationResponse(result=result, mask=mask)
        
        assert len(response.result) == 4
        assert len(response.result[0]) == 1

    def test_aggregation_response_to_dict_structure(self):
        """Test dict structure is correct."""
        result = [[0.5, 0.5]]
        mask = [[1, 0]]
        response = AggregationResponse(result=result, mask=mask)
        
        result_dict = response.to_dict()
        
        # Verify it can be serialized (JSON-like structure)
        assert isinstance(result_dict['result'], list)
        assert isinstance(result_dict['mask'], list)

    def test_aggregation_response_from_arrays_precision(self):
        """Test precision is maintained in conversion."""
        df_matrix = np.array([[0.123456789]], dtype=np.float32)
        room_mask = np.array([[1]], dtype=np.uint8)
        
        response = AggregationResponse.from_arrays(df_matrix, room_mask)
        
        # Value should be preserved (within float32 precision)
        assert response.result[0][0] == pytest.approx(0.123456789, rel=1e-5)

    def test_aggregation_response_rectangular_array(self):
        """Test with rectangular (non-square) arrays."""
        df_matrix = np.random.rand(20, 30).astype(np.float32)
        room_mask = np.ones((20, 30), dtype=np.uint8)
        
        response = AggregationResponse.from_arrays(df_matrix, room_mask)
        
        assert len(response.result) == 20
        assert len(response.result[0]) == 30
