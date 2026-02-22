"""OpenAPI specification generator from Pydantic models for auto-documentation"""

from typing import Dict, Any
from src.__version__ import version as app_version
from src.server.schemas import (
    MergeRequest,
    MergeResponse,
    ErrorResponse,
)


class OpenAPISpecGenerator:
    """Generates OpenAPI 3.0 specification for Flask API using Pydantic models"""

    @staticmethod
    def generate_spec(
        title: str = "Server Merger API",
        description: str = "Daylight Factor aggregation/merge service for combining multiple window simulations",
        version: str = app_version,
        base_url: str = "/"
    ) -> Dict[str, Any]:
        """
        Generate OpenAPI 3.0 specification from Pydantic models.

        Args:
            title: API title
            description: API description
            version: API version
            base_url: Base URL for API endpoints

        Returns:
            OpenAPI 3.0 specification dict
        """
        return {
            "openapi": "3.0.0",
            "info": {
                "title": title,
                "description": description,
                "version": version,
                "contact": {
                    "name": "API Support"
                }
            },
            "servers": [
                {
                    "url": base_url,
                    "description": "Server API"
                }
            ],
            "paths": OpenAPISpecGenerator._generate_paths(),
            "components": {
                "schemas": OpenAPISpecGenerator._generate_schemas()
            }
        }

    @staticmethod
    def _generate_paths() -> Dict[str, Any]:
        """Generate API paths from endpoint definitions"""
        return {
            "/": {
                "get": {
                    "summary": "Get server status",
                    "description": "Returns server status information",
                    "tags": ["Status"],
                    "responses": {
                        "200": {
                            "description": "Success - Server status",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "status": {"type": "string"},
                                            "service": {"type": "string"}
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "/merge": {
                "post": {
                    "summary": "Merge/Aggregate DF simulations",
                    "description": "Aggregate daylight factor values from multiple window simulations into a single room polygon representation",
                    "tags": ["Aggregation"],
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/MergeRequest"}
                            }
                        }
                    },
                    "responses": {
                        "200": {
                            "description": "Success - Aggregated DF matrix and mask",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/MergeResponse"}
                                }
                            }
                        },
                        "400": {
                            "description": "Validation error",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/ErrorResponse"}
                                }
                            }
                        },
                        "500": {
                            "description": "Server error",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/ErrorResponse"}
                                }
                            }
                        }
                    }
                }
            }
        }

    @staticmethod
    def _generate_schemas() -> Dict[str, Any]:
        """Generate component schemas from Pydantic models"""
        return {
            "MergeRequest": MergeRequest.model_json_schema(),
            "MergeResponse": MergeResponse.model_json_schema(),
            "ErrorResponse": ErrorResponse.model_json_schema(),
        }
