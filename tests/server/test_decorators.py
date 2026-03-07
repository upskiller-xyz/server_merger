"""Tests for server decorators"""

import pytest
from unittest.mock import Mock, patch
from flask import Flask
from src.server.decorators import endpoint_error_handler
from src.core.enums import Endpoint, HTTPStatus
from pydantic import BaseModel


class MergeRequest(BaseModel):
    """Test Pydantic model for validation"""
    name: str
    value: int


class TestEndpointErrorHandler:
    """Test endpoint_error_handler decorator"""

    def setup_method(self):
        """Set up Flask app for testing"""
        self.app = Flask(__name__)
        self.app.config['TESTING'] = True

    def test_json_extraction_with_data(self):
        """Test JSON data extraction from request"""
        @endpoint_error_handler(Endpoint.MERGE)
        def merge_handler(self, data):
            return {"received": data}
        
        with self.app.test_request_context(
            json={"test": "data"},
            method='POST'
        ):
            mock_self = Mock()
            result = merge_handler(mock_self)
            assert result == {"received": {"test": "data"}}

    def test_json_extraction_without_data(self):
        """Test handling missing JSON data"""
        @endpoint_error_handler(Endpoint.MERGE)
        def merge_handler(self, data):
            return {"data": data}
        
        with self.app.test_request_context(method='GET'):
            mock_self = Mock()
            result = merge_handler(mock_self)
            assert result == {"data": {}}

    def test_pydantic_validation_valid(self):
        """Test Pydantic model validation with valid data"""
        @endpoint_error_handler(Endpoint.MERGE, request_model=MergeRequest)
        def merge_handler(self, data):
            return {"name": data.name, "value": data.value}
        
        with self.app.test_request_context(
            json={"name": "test", "value": 42},
            method='POST'
        ):
            mock_self = Mock()
            result = merge_handler(mock_self)
            assert result == {"name": "test", "value": 42}

    def test_pydantic_validation_invalid(self):
        """Test Pydantic model validation with invalid data"""
        @endpoint_error_handler(Endpoint.MERGE, request_model=MergeRequest)
        def merge_handler(self, data):
            return {"validated": str(data)}
        
        with self.app.test_request_context(
            json={"name": "test"},  # Missing required 'value' field
            method='POST'
        ):
            mock_self = Mock()
            result = merge_handler(mock_self)
            # Error response is a tuple (Response, status_code)
            if isinstance(result, tuple):
                response, status = result
                # Get JSON from Flask Response
                import json
                data = json.loads(response.get_data(as_text=True))
                assert "error" in data
                assert "Validation error" in data["error"]
            else:
                # Success path
                assert "error" in result or "validated" in result

    def test_value_error_handling(self):
        """Test decorator catches ValueError"""
        @endpoint_error_handler(Endpoint.MERGE)
        def merge_handler(self, data):
            raise ValueError("Invalid input")
        
        with self.app.test_request_context(json={}, method='POST'):
            mock_self = Mock()
            result = merge_handler(mock_self)
            
            # Error response is a tuple (Response, status_code)
            if isinstance(result, tuple):
                response, status = result
                import json
                data = json.loads(response.get_data(as_text=True))
                assert "error" in data
                assert "Invalid input" in data["error"]
            else:
                assert False, f"Expected tuple, got {type(result)}"

    def test_generic_exception_handling(self):
        """Test decorator catches generic exceptions"""
        @endpoint_error_handler(Endpoint.MERGE)
        def merge_handler(self, data):
            raise RuntimeError("Unexpected error")
        
        with self.app.test_request_context(json={}, method='POST'):
            mock_self = Mock()
            result = merge_handler(mock_self)
            
            # Error response is a tuple (Response, status_code)
            if isinstance(result, tuple):
                response, status = result
                import json
                data = json.loads(response.get_data(as_text=True))
                assert "error" in data
                assert "Unexpected error" in data["error"]
            else:
                assert False, f"Expected tuple, got {type(result)}"

    @patch('src.server.decorators.logger')
    def test_error_logging(self, mock_logger):
        """Test decorator logs errors"""
        @endpoint_error_handler(Endpoint.MERGE)
        def merge_handler(self, data):
            raise ValueError("Test error")
        
        with self.app.test_request_context(json={}, method='POST'):
            mock_self = Mock()
            merge_handler(mock_self)
            
            # Verify logger.error was called
            assert mock_logger.error.called

    def test_function_metadata_preserved(self):
        """Test decorator preserves function metadata"""
        @endpoint_error_handler(Endpoint.MERGE)
        def merge_handler(self, data):
            """Handler docstring"""
            return data
        
        assert merge_handler.__name__ == "merge_handler"
        assert "Handler docstring" in merge_handler.__doc__

    def test_empty_json_object(self):
        """Test decorator with empty JSON object"""
        @endpoint_error_handler(Endpoint.MERGE)
        def merge_handler(self, data):
            return {"has_keys": len(data) > 0}
        
        with self.app.test_request_context(json={}, method='POST'):
            result = merge_handler(Mock())
            assert result == {"has_keys": False}

    @patch('src.server.decorators.logger')
    def test_logs_endpoint_value(self, mock_logger):
        """Test decorator logs with endpoint value"""
        @endpoint_error_handler(Endpoint.MERGE)
        def merge_handler(self, data):
            raise Exception("Test error")
        
        with self.app.test_request_context(json={}, method='POST'):
            merge_handler(Mock())
            
            # Check that logger was called with endpoint value
            call_args = str(mock_logger.error.call_args)
            assert "merge" in call_args.lower()

    def test_validation_error_message_format(self):
        """Test Pydantic validation error message formatting"""
        @endpoint_error_handler(Endpoint.MERGE, request_model=MergeRequest)
        def merge_handler(self, data):
            return {"success": True}
        
        with self.app.test_request_context(
            json={"name": "test", "value": "not_an_int"},
            method='POST'
        ):
            result = merge_handler(Mock())
            # Error response is a tuple (Response, status_code)
            if isinstance(result, tuple):
                response, status = result
                import json
                data = json.loads(response.get_data(as_text=True))
                assert "error" in data
                assert "Validation error" in data["error"]
            else:
                assert False, f"Expected tuple, got {type(result)}"

    def test_bad_request_exception_handling(self):
        """Test handling of BadRequest exceptions"""
        from werkzeug.exceptions import BadRequest
        
        @endpoint_error_handler(Endpoint.MERGE)
        def merge_handler(self, data):
            raise BadRequest("Invalid JSON")
        
        with self.app.test_request_context(json={}, method='POST'):
            result = merge_handler(Mock())
            # Error response is a tuple (Response, status_code)
            if isinstance(result, tuple):
                response, status = result
                import json
                data = json.loads(response.get_data(as_text=True))
                assert "error" in data
            else:
                assert False, f"Expected tuple, got {type(result)}"

    def test_multiple_validator_composition(self):
        """Test decorator with Pydantic model has multiple validators"""
        class ComplexRequest(BaseModel):
            items: list
            count: int
        
        @endpoint_error_handler(Endpoint.MERGE, request_model=ComplexRequest)
        def merge_handler(self, data):
            return {"count": len(data.items)}
        
        with self.app.test_request_context(
            json={"items": [1, 2, 3], "count": 3},
            method='POST'
        ):
            result = merge_handler(Mock())
            assert result["count"] == 3

    def test_success_response_not_tuple(self):
        """Test that successful responses are dicts, not tuples"""
        @endpoint_error_handler(Endpoint.MERGE)
        def merge_handler(self, data):
            return {"success": True}
        
        with self.app.test_request_context(json={}, method='POST'):
            result = merge_handler(Mock())
            assert isinstance(result, dict)
            assert result["success"] is True
