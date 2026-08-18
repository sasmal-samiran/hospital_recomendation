import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger(__name__)

def create_error_response(
    status_code: int,
    code: str,
    message: str,
    details: Optional[Any] = None,
    service: Optional[str] = None,
    path: Optional[str] = None
) -> JSONResponse:
    """Standardized JSON error envelope for frontend consumption."""
    error_body: Dict[str, Any] = {
        "code": code,
        "message": message,
    }
    if service:
        error_body["service"] = service
    if details is not None:
        error_body["details"] = details

    content = {
        "success": False,
        "error": error_body,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "path": path
    }
    return JSONResponse(status_code=status_code, content=content)

class AppBaseException(Exception):
    """Base application exception."""
    def __init__(
        self,
        message: str,
        code: str = "APPLICATION_ERROR",
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        details: Optional[Any] = None
    ):
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details

class ExternalAPIError(AppBaseException):
    """Exception raised when an upstream external API fails."""
    def __init__(
        self,
        service_name: str,
        message: str,
        status_code: int = status.HTTP_502_BAD_GATEWAY,
        upstream_status_code: Optional[int] = None,
        details: Optional[Any] = None
    ):
        super().__init__(
            message=f"{service_name} Error: {message}",
            code="EXTERNAL_API_ERROR",
            status_code=status_code,
            details={
                "service": service_name,
                "upstream_status_code": upstream_status_code,
                "upstream_details": details
            }
        )
        self.service_name = service_name
        self.upstream_status_code = upstream_status_code

class ResourceNotFoundError(AppBaseException):
    """Exception raised when requested resource or entity is not found."""
    def __init__(self, resource_name: str, message: str, details: Optional[Any] = None):
        super().__init__(
            message=message,
            code="RESOURCE_NOT_FOUND",
            status_code=status.HTTP_404_NOT_FOUND,
            details={"resource": resource_name, "details": details}
        )

class ImageProcessingError(AppBaseException):
    """Exception raised when an image cannot be fetched, decoded, or processed."""
    def __init__(self, message: str, details: Optional[Any] = None):
        super().__init__(
            message=message,
            code="IMAGE_PROCESSING_ERROR",
            status_code=status.HTTP_400_BAD_REQUEST,
            details=details
        )

class InvalidInputError(AppBaseException):
    """Exception raised for domain-specific business validation failures."""
    def __init__(self, message: str, details: Optional[Any] = None):
        super().__init__(
            message=message,
            code="INVALID_INPUT",
            status_code=status.HTTP_400_BAD_REQUEST,
            details=details
        )

def register_exception_handlers(app: FastAPI) -> None:
    """Register uniform global exception handlers on the FastAPI app."""

    @app.exception_handler(AppBaseException)
    async def app_base_exception_handler(request: Request, exc: AppBaseException):
        logger.error(f"AppBaseException [{exc.code}] on {request.url.path}: {exc.message}")
        service = getattr(exc, "service_name", None)
        return create_error_response(
            status_code=exc.status_code,
            code=exc.code,
            message=exc.message,
            details=exc.details,
            service=service,
            path=request.url.path
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        logger.warning(f"RequestValidationError on {request.url.path}: {exc.errors()}")
        formatted_errors: List[Dict[str, Any]] = []
        for err in exc.errors():
            loc = " -> ".join([str(l) for l in err.get("loc", []) if l != "body"])
            formatted_errors.append({
                "field": loc or "body",
                "message": err.get("msg", "Invalid input value"),
                "type": err.get("type", "validation_error")
            })

        return create_error_response(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            code="VALIDATION_ERROR",
            message="Request body or query parameters failed validation.",
            details=formatted_errors,
            path=request.url.path
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        logger.warning(f"HTTPException {exc.status_code} on {request.url.path}: {exc.detail}")
        return create_error_response(
            status_code=exc.status_code,
            code=f"HTTP_{exc.status_code}",
            message=str(exc.detail),
            path=request.url.path
        )

    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        logger.exception(f"Unhandled Internal Server Error on {request.url.path}: {exc}")
        return create_error_response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            code="INTERNAL_SERVER_ERROR",
            message="An unexpected internal server error occurred while processing your request.",
            details=str(exc),
            path=request.url.path
        )
