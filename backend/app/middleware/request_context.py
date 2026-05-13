import uuid
import time
import structlog
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = structlog.get_logger()


class RequestContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        request.state.start_time = time.time()

        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(
            request_id=request_id,
            method=request.method,
            path=str(request.url.path),
        )

        logger.info("request_started")

        try:
            response = await call_next(request)
            response.headers["X-Request-ID"] = request_id
        except Exception as exc:
            logger.error("request_failed", error=str(exc))
            raise

        elapsed = time.time() - request.state.start_time
        logger.info(
            "request_completed",
            status_code=response.status_code,
            duration_ms=round(elapsed * 1000, 2),
        )

        response.headers["X-Response-Time-Ms"] = str(round(elapsed * 1000, 2))
        return response
