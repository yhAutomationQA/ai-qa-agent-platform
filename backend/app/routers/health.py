import time
import structlog
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.core.database import get_db

logger = structlog.get_logger()
router = APIRouter()


@router.get("")
async def health():
    return {
        "status": "healthy",
        "service": "ai-qa-platform-backend",
        "version": "1.0.0",
        "timestamp": time.time(),
    }


@router.get("/ready")
async def readiness(db: AsyncSession = Depends(get_db)):
    db_ok = False
    try:
        await db.execute(text("SELECT 1"))
        db_ok = True
    except Exception as e:
        logger.error("health_db_check_failed", error=str(e))

    if not db_ok:
        from fastapi import status
        from starlette.responses import JSONResponse
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "unhealthy",
                "service": "ai-qa-platform-backend",
                "checks": {
                    "database": "unreachable",
                },
            },
        )

    return {
        "status": "healthy",
        "service": "ai-qa-platform-backend",
        "checks": {
            "database": "connected",
        },
        "timestamp": time.time(),
    }


@router.get("/live")
async def liveness():
    return {
        "status": "alive",
        "service": "ai-qa-platform-backend",
        "timestamp": time.time(),
    }
