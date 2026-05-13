from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.config import settings
from app.core.logging import setup_logging
from app.core.exceptions import BaseAppException
from app.middleware.request_context import RequestContextMiddleware
from app.middleware.error_handler import (
    app_exception_handler,
    validation_exception_handler,
    http_exception_handler,
    unhandled_exception_handler,
)
from app.routers import router as health_router
from app.routers.v1 import router as v1_router

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    logger.info(
        "app_starting",
        app_name=settings.APP_NAME,
        environment=settings.APP_ENV,
    )
    yield
    logger.info("app_shutting_down")


app = FastAPI(
    title=settings.APP_NAME,
    description="Enterprise-grade AI-powered testing and quality assurance platform",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
    terms_of_service="https://example.com/terms",
    contact={
        "name": "AI QA Platform Team",
        "url": "https://example.com/support",
        "email": "support@example.com",
    },
    license_info={
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT",
    },
)

# ─────────────────────────────────────────────
# Middleware (order matters — outermost first)
# ─────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID", "X-Response-Time-Ms"],
    max_age=600,
)
app.add_middleware(RequestContextMiddleware)

# ─────────────────────────────────────────────
# Exception handlers
# ─────────────────────────────────────────────
app.add_exception_handler(BaseAppException, app_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(Exception, unhandled_exception_handler)

# ─────────────────────────────────────────────
# Routers
# ─────────────────────────────────────────────
app.include_router(health_router, prefix="/api")
app.include_router(v1_router, prefix="/api/v1")


@app.get("/", tags=["root"])
async def root():
    return {
        "app": settings.APP_NAME,
        "version": "1.0.0",
        "docs": "/docs",
        "openapi": "/openapi.json",
    }
