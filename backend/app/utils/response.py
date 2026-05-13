from typing import Any, Generic, TypeVar
from dataclasses import dataclass

from fastapi.encoders import jsonable_encoder
from starlette.responses import JSONResponse

T = TypeVar("T")


@dataclass
class ResponseWrapper(Generic[T]):
    success: bool
    data: T | None = None
    error: dict | None = None
    meta: dict | None = None


def success_response(
    data: Any = None,
    message: str = "Success",
    status_code: int = 200,
    meta: dict | None = None,
) -> JSONResponse:
    body: dict[str, Any] = {
        "success": True,
        "message": message,
        "data": jsonable_encoder(data) if data is not None else None,
    }
    if meta:
        body["meta"] = meta
    return JSONResponse(content=body, status_code=status_code)


def error_response(
    message: str = "Error",
    error_code: str = "INTERNAL_ERROR",
    status_code: int = 500,
    details: Any = None,
) -> JSONResponse:
    body: dict[str, Any] = {
        "success": False,
        "error": {
            "code": error_code,
            "message": message,
        },
    }
    if details:
        body["error"]["details"] = details
    return JSONResponse(content=body, status_code=status_code)


def paginated_response(
    items: list[Any],
    total: int,
    page: int,
    page_size: int,
    message: str = "Success",
) -> JSONResponse:
    return success_response(
        data=items,
        message=message,
        meta={
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total": total,
                "total_pages": max(1, (total + page_size - 1) // page_size),
            }
        },
    )
