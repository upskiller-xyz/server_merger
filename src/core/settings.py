"""Global application settings

Reads configuration from environment variables (.env file or system environment).
"""

import os
from pathlib import Path


class ApplicationSettings:
    """Global application settings singleton"""
    
    # Image saving configuration
    SAVE_IMAGES: bool = os.getenv("SAVE_IMAGES", "false").lower() in ("true", "1", "yes")
    
    # Image output directory
    IMAGES_OUTPUT_DIR: str = os.getenv("IMAGES_OUTPUT_DIR", "../outputs")
    
    # Server configuration
    DEBUG: bool = os.getenv("DEBUG", "false").lower() in ("true", "1", "yes")
    PORT: int = int(os.getenv("PORT", "8084"))


# Global settings instance
settings = ApplicationSettings()
