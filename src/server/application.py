"""Server application implementation"""

from typing import Dict, Any
from pathlib import Path
from flask import Flask, Response, jsonify, render_template
from flask_cors import CORS
import logging

from src.core.enums import ServiceName, Endpoint, HTTPStatus
from src.server.controllers.base_controller import ServerController
from src.server.services.df_aggregation_service import DFAggregationService
from src.server.services.validation import ValidationError
from src.server.services.validation.request import DFAggregationRequestValidator, RequestField
from src.server.decorators import endpoint_error_handler
from src.server.openapi import OpenAPISpecGenerator

logger = logging.getLogger("logger")


class ServerConfig:
    """Server configuration constants"""
    DEFAULT_OUTPUT_SCALE = 0.1


class ServerApplication:
    """Main application class implementing dependency injection and OOP principles"""

    def __init__(self, app_name: str = "Server Application") -> None:
        """
        Initialize the Flask application with dependencies.

        Args:
            app_name: Name of the Flask application
        """
        # Set template folder to src/server/templates
        template_folder = Path(__file__).parent / "templates"
        self._app: Flask = Flask(app_name, template_folder=str(template_folder))
        CORS(self._app)
        self._controller: ServerController | None = None
        self._request_validator = DFAggregationRequestValidator()
        self._setup_dependencies()
        self._setup_routes()

    def _setup_dependencies(self) -> None:
        """Setup all dependencies using dependency injection"""
        # Only configure logging if no handlers are already set up
        if not logging.root.handlers:
            logging.basicConfig(
                level=logging.DEBUG,
                format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )

        # DF Aggregation Service
        df_service = DFAggregationService(output_scale=ServerConfig.DEFAULT_OUTPUT_SCALE)

        services = {
            ServiceName.DF_AGGREGATION.value: df_service
        }

        # Controller
        self._controller = ServerController(services=services)

        # Initialize controller
        self._controller.initialize()

    def _setup_routes(self) -> None:
        """Setup Flask routes"""
        self._app.add_url_rule("/", "get_status", self._get_status, methods=["GET"])
        self._app.add_url_rule("/merge", "merge", self._aggregate_df, methods=["POST"])

        # Documentation endpoints
        self._app.add_url_rule("/openapi.json", "openapi_spec", self._openapi_spec, methods=["GET"])
        self._app.add_url_rule("/docs", "swagger_ui", self._swagger_ui, methods=["GET"])
        self._app.add_url_rule("/redoc", "redoc", self._redoc, methods=["GET"])

    def _get_status(self) -> Dict[str, Any]:
        """
        Get server status endpoint.

        Returns:
            JSON response with server status information
        """
        return jsonify(self._controller.get_status()) # type: ignore

    @endpoint_error_handler(Endpoint.MERGE)
    def _aggregate_df(self, data: Dict[str, Any]) -> tuple:
        """
        Aggregate daylight factor values from multiple window simulations.

        Expected JSON payload:
        {
            "room_polygon": [[x1, y1], [x2, y2], ...],
            "windows": {
                "window1": {
                    "x1": float, "y1": float, "z1": float,
                    "x2": float, "y2": float, "z2": float,
                    "direction_angle": float
                },
                ...
            },
            "simulation": {
                "window1": {
                    "df_values": [[...], [...], ...],
                    "mask": [[...], [...], ...]
                },
                ...
            }
        }

        Returns:
            tuple: (response, status_code) with aggregated result and mask
        """
        # Validate request with detailed error messages
        try:
            self._request_validator.validate(data)
        except ValidationError as e:
            # Return structured validation error
            logger.warning(f"Validation error: {e.message}")
            return jsonify(e.to_dict()), HTTPStatus.BAD_REQUEST.value

        # Get DF aggregation service
        df_service = self._controller.get_service(ServiceName.DF_AGGREGATION.value) # type: ignore

        # Process request
        result = df_service.process_request(
            room_polygon=data[RequestField.ROOM_POLYGON.value],
            windows_data=data[RequestField.WINDOWS.value],
            simulations=data[RequestField.SIMULATION.value]
        )

        logger.info("DF aggregation successful")
        return jsonify(result), HTTPStatus.OK.value

    def _openapi_spec(self) -> Response:
        """
        Return OpenAPI 3.0 specification.

        Returns:
            JSON with complete API specification
        """
        spec = OpenAPISpecGenerator.generate_spec()
        return jsonify(spec)

    def _swagger_ui(self) -> str:
        """
        Return Swagger UI HTML.

        Interactive API documentation at /docs
        """
        return render_template("swagger.html")

    def _redoc(self) -> str:
        """
        Return ReDoc HTML.

        Alternative interactive API documentation at /redoc
        """
        return render_template("redoc.html")

    @property
    def app(self) -> Flask:
        """
        Get Flask application instance.

        Returns:
            Flask: The Flask application object
        """
        return self._app
