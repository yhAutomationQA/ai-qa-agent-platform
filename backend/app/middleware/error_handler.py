import structlog
from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.exceptions import BaseAppException

logger = structlog.get_logger()


async def app_exception_handler(request: Request, exc: BaseAppException) -> JSONResponse:
    logger.warning(
        "app_exception",
        status_code=exc.status_code,
        detail=exc.detail,
        path=str(request.url.path),
        method=request.method,
    )
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": {
                "code": getattr(exc.detail, "get", lambda k: None)("error_code") if isinstance(exc.detail, dict) else None,
                "message": exc.detail.get("message") if isinstance(exc.detail, dict) else str(exc.detail),
            },
            "request_id": getattr(request.state, "request_id", None),
        },
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    errors = exc.errors()
    logger.warning(
        "validation_error",
        errors=errors,
        path=str(request.url.path),
        method=request.method,
    )
    return JSONResponse(
        status_code=422,
        content={
            "success": False,
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Request validation failed",
                "details": [
                    {
                        "field": " -> ".join(str(loc) for loc in e.get("loc", [])),
                        "message": e.get("msg", ""),
                        "type": e.get("type", ""),
                    }
                    for e in errors
                ],
            },
            "request_id": getattr(request.state, "request_id", None),
        },
    )


async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    logger.warning(
        "http_exception",
        status_code=exc.status_code,
        detail=exc.detail,
        path=str(request.url.path),
    )
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": {
                "code": "HTTP_ERROR",
                "message": str(exc.detail),
            },
            "request_id": getattr(request.state, "request_id", None),
        },
    )


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.error(
        "unhandled_exception",
        error=str(exc),
        path=str(request.url.path),
        method=request.method,
        exc_info=True,
    )
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "An unexpected error occurred",
            },
            "request_id": getattr(request.state, "request_id", None),
        },
    )
