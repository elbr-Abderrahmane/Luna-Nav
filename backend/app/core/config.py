"""Application configuration and logging setup for LUNA NAV Backend.

Uses standard library + python-dotenv and Pydantic BaseModel so that configuration
remains validated and strongly typed without requiring extra external dependencies.
"""

import logging
import os
from pathlib import Path
from typing import List

from dotenv import load_dotenv
from pydantic import BaseModel, Field

# Load environment variables from .env if present
BASE_DIR = Path(__file__).resolve().parent.parent.parent
load_dotenv(BASE_DIR / ".env")


class Settings(BaseModel):
    """Application-wide configuration settings."""

    app_name: str = Field(default="LUNA NAV — Lunar Landing Site Navigator API")
    app_version: str = Field(default="0.1.0-provisional")
    environment: str = Field(default_factory=lambda: os.getenv("LUNA_ENV", "development"))
    debug: bool = Field(
        default_factory=lambda: os.getenv("LUNA_DEBUG", "true").lower() in ("1", "true", "yes")
    )
    api_prefix: str = Field(default_factory=lambda: os.getenv("LUNA_API_PREFIX", "/api"))
    log_level: str = Field(default_factory=lambda: os.getenv("LUNA_LOG_LEVEL", "INFO").upper())

    # Adapter mode flags: allow individual scientific modules to be toggled from mock to real
    use_mock_terrain: bool = Field(
        default_factory=lambda: os.getenv("USE_MOCK_TERRAIN", "true").lower() in ("1", "true", "yes")
    )
    use_mock_astronomy: bool = Field(
        default_factory=lambda: os.getenv("USE_MOCK_ASTRONOMY", "true").lower() in ("1", "true", "yes")
    )
    use_mock_decision: bool = Field(
        default_factory=lambda: os.getenv("USE_MOCK_DECISION", "true").lower() in ("1", "true", "yes")
    )

    # CORS origins for Person 1's 3D Frontend
    cors_origins: List[str] = Field(
        default_factory=lambda: [
            origin.strip()
            for origin in os.getenv(
                "LUNA_CORS_ORIGINS",
                "http://localhost:3000,http://localhost:5173,http://127.0.0.1:3000,http://127.0.0.1:5173",
            ).split(",")
            if origin.strip()
        ]
    )

    # Paths for mock data and generated PDF reports
    mock_data_dir: Path = Field(
        default_factory=lambda: Path(
            os.getenv("LUNA_MOCK_DATA_DIR", str(BASE_DIR / "app" / "mock_data"))
        )
    )
    reports_output_dir: Path = Field(
        default_factory=lambda: Path(
            os.getenv("LUNA_REPORTS_DIR", str(BASE_DIR / "generated_reports"))
        )
    )


def configure_logging(log_level: str = "INFO") -> None:
    """Configure structured standard logging for the application."""
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)
    logging.basicConfig(
        level=numeric_level,
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%SZ",
    )


settings = Settings()
configure_logging(settings.log_level)
logger = logging.getLogger("luna_nav")
