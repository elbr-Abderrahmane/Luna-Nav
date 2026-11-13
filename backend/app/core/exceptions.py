"""Custom domain exceptions and FastAPI exception handlers for LUNA NAV.

Provides consistent JSON error responses across all endpoints so Person 1 (Frontend)
can reliably parse error codes, messages, and details.
"""

import logging
from typing import Any, Dict, Optional

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

logger = logging.getLogger("luna_nav.exceptions")


class LunaNavException(Exception):
    """Base exception for all LUNA NAV domain errors."""

    def __init__(
        self,
        message: str,
        error_code: str = "LUNA_NAV_ERROR",
        status_code: int = status.HTTP_400_BAD_REQUEST,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        self.details = details or {}


class ResourceNotFoundError(LunaNavException):
    """Raised when a requested mission, region, zone, point, or report does not exist."""

    def __init__(
        self,
        resource_type: str,
        resource_id: str,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(
            message=f"{resource_type} with id '{resource_id}' was not found.",
            error_code="RESOURCE_NOT_FOUND",
            status_code=status.HTTP_404_NOT_FOUND,
            details={"resource_type": resource_type, "resource_id": resource_id, **(details or {})},
        )


class DomainValidationError(LunaNavException):
    """Raised when domain-level business rules fail (e.g., invalid zone count or incompatible region)."""

    def __init__(
        self,
        message: str,
        error_code: str = "DOMAIN_VALIDATION_ERROR",
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(
            message=message,
            error_code=error_code,
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            details=details,
        )


class AdapterIntegrationError(LunaNavException):
    """Raised when an external scientific adapter (Terrain, Astronomy, Decision) fails or is unconfigured."""

    def __init__(
        self,
        adapter_name: str,
        message: str,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(
            message=f"Integration error in {adapter_name}: {message}",
            error_code="ADAPTER_INTEGRATION_ERROR",
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            details={"adapter": adapter_name, **(details or {})},
        )


def register_exception_handlers(app: FastAPI) -> None:
    """Register unified exception handlers on the FastAPI application instance."""

    @app.exception_handler(LunaNavException)
    async def luna_nav_exception_handler(request: Request, exc: LunaNavException) -> JSONResponse:
        logger.warning(
            "Domain exception on %s %s [%s]: %s",
            request.method,
            request.url.path,
            exc.error_code,
            exc.message,
        )
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {
                    "code": exc.error_code,
                    "message": exc.message,
                    "details": exc.details,
                    "path": request.url.path,
                }
            },
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        logger.warning(
            "Pydantic validation error on %s %s: %s",
            request.method,
            request.url.path,
            exc.errors(),
        )
        sanitized_errors = []
        for err in exc.errors():
            err_copy = dict(err)
            if "ctx" in err_copy and isinstance(err_copy["ctx"], dict):
                err_copy["ctx"] = {k: str(v) for k, v in err_copy["ctx"].items()}
            sanitized_errors.append(err_copy)

        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            content={
                "error": {
                    "code": "REQUEST_VALIDATION_ERROR",
                    "message": "Input validation failed. Check 'details.errors' for field-level issues.",
                    "details": {"errors": sanitized_errors},
                    "path": request.url.path,
                }
            },
        )
