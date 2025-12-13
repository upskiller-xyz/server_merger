import os
from typing import Dict, Any

# Disable GPU/CUDA to prevent bus errors on WSL2
os.environ['CUDA_VISIBLE_DEVICES'] = '-1'
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
os.environ['OPENCV_IO_ENABLE_OPENEXR'] = '0'
os.environ['OMP_NUM_THREADS'] = '1'

import sys
from pathlib import Path
import logging
from enum import Enum

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.exceptions import BadRequest

from src.server.enums import ContentType, HTTPStatus, LogLevel
from src.server.services.logging import StructuredLogger
from src.server.controllers.base_controller import ServerController
from src.server.services.df_aggregation import DFAggregationService


class ServerConfig:
    """Server configuration constants"""
    DEFAULT_HOST = "0.0.0.0"
    DEFAULT_PORT = 8080
    DEFAULT_ENV_PORT = 8081
    DEFAULT_OUTPUT_SCALE = 0.1


class ServiceName(Enum):
    """Service name enumeration"""
    DF_AGGREGATION = "df_aggregation"


class RequestField(Enum):
    """Request field names"""
    ROOM_POLYGON = "room_polygon"
    WINDOWS = "windows"
    SIMULATIONS = "simulations"




class ServerApplication:
    """Main application class implementing dependency injection and OOP principles"""

    def __init__(self, app_name: str = "Server Application"):
        self._app = Flask(app_name)
        CORS(self._app)
        self._controller = None
        self._logger = None
        self._setup_dependencies()
        self._setup_routes()

    def _setup_dependencies(self) -> None:
        """Setup all dependencies using dependency injection"""
        # Configure root logger for detailed debugging
        logging.basicConfig(
            level=logging.DEBUG,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

        # Logger
        self._logger = StructuredLogger("Server", LogLevel.INFO)

        # DF Aggregation Service
        df_service = DFAggregationService(output_scale=ServerConfig.DEFAULT_OUTPUT_SCALE)

        services = {
            ServiceName.DF_AGGREGATION.value: df_service
        }

        # Controller
        self._controller = ServerController(
            logger=self._logger,
            services=services
        )

        # Initialize controller
        self._controller.initialize()

    def _setup_routes(self) -> None:
        """Setup Flask routes"""
        self._app.add_url_rule("/", "get_status", self._get_status, methods=["GET"])
        self._app.add_url_rule("/route_example", "route_example", self._route_example, methods=["POST"])
        self._app.add_url_rule("/merge", "merge", self._aggregate_df, methods=["POST"])

    def _get_status(self) -> Dict[str, Any]:
        """Get server status endpoint"""
        return jsonify(self._controller.get_status())

    def _route_example(self) -> Dict[str, Any]:
        """Run prediction endpoint"""
        # Check if file was uploaded
        if 'file' not in request.files:
            raise BadRequest("No file uploaded")

        file = request.files['file']

        # Validate content type
        # remove if using other input types
        if not ContentType.is_image(file.content_type):
            raise BadRequest("File must be an image")

        try:
            # endpoint logic

            result = {}

            # Check for errors
            if result.get("status") == "error":
                return jsonify(result), HTTPStatus.INTERNAL_SERVER_ERROR.value

            return jsonify(result)

        except Exception as e:
            return jsonify({"error": f"Prediction failed: {str(e)}"}), HTTPStatus.INTERNAL_SERVER_ERROR.value

    def _aggregate_df(self) -> Dict[str, Any]:
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
            "simulations": {
                "window1": {
                    "df_values": [[...], [...], ...],  # 384x384 or 128x128
                    "mask": [[...], [...], ...]         # Same dimensions
                },
                ...
            }
        }

        Returns:
        {
            "df_matrix": [[...], [...], ...],
            "room_mask": [[...], [...], ...]
        }
        """
        try:
            # Get JSON data
            data = request.get_json()

            if not data:
                raise BadRequest("No JSON data provided")

            # Validate required fields
            required_fields = [
                RequestField.ROOM_POLYGON.value,
                RequestField.WINDOWS.value,
                RequestField.SIMULATIONS.value
            ]
            for field in required_fields:
                if field not in data:
                    raise BadRequest(f"Missing required field: {field}")

            # Get DF aggregation service
            df_service = self._controller.get_service(ServiceName.DF_AGGREGATION.value)

            # Process request
            result = df_service.process_request(
                room_polygon=data[RequestField.ROOM_POLYGON.value],
                windows_data=data[RequestField.WINDOWS.value],
                simulations=data[RequestField.SIMULATIONS.value]
            )

            return jsonify(result)

        except ValueError as e:
            return jsonify({"error": f"Validation error: {str(e)}"}), HTTPStatus.BAD_REQUEST.value
        except Exception as e:
            self._logger.error(f"DF aggregation failed: {str(e)}")
            return jsonify({"error": f"Aggregation failed: {str(e)}"}), HTTPStatus.INTERNAL_SERVER_ERROR.value

    @property
    def app(self) -> Flask:
        """Get Flask application instance"""
        return self._app


class ServerLauncher:
    """Launcher class for the server application"""

    @staticmethod
    def create_application() -> ServerApplication:
        """Create and configure the application"""
        return ServerApplication()

    @staticmethod
    def run_server(
        app: ServerApplication,
        host: str = ServerConfig.DEFAULT_HOST,
        port: int = ServerConfig.DEFAULT_PORT,
        debug: bool = True
    ) -> None:
        """Run the server"""
        """Run the server"""
        log_msg = (
            f"Flask app '{app.app.name}' starting on "
            f"host {host}, port {port}. Debug mode: {debug}"
        )
        app.app.logger.info(log_msg)
        # Disable reloader to prevent bus errors/hangs on WSL2
        app.app.run(host=host, port=port, debug=debug, use_reloader=False)


def main() -> None:
    """Main entry point"""
    launcher = ServerLauncher()
    application = launcher.create_application()
    port = int(os.getenv("PORT", ServerConfig.DEFAULT_ENV_PORT))
    launcher.run_server(application, port=port, debug=True)


# Create app instance for gunicorn only when needed
# Don't create at module import time to avoid bus errors
def create_app():
    """Factory function for creating the Flask app (for gunicorn)"""
    _application = ServerApplication()
    return _application.app


# Only create app instance if not running as main (i.e., when imported by gunicorn)
if __name__ != "__main__":
    app = create_app()
else:
    # Running as main script
    main()