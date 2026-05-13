from fastapi import APIRouter

router = APIRouter()


@router.get("/health", include_in_schema=False)
async def deprecated_health():
    return {"status": "healthy", "service": "ai-qa-platform", "version": "1.0.0"}


@router.get("/health/database", include_in_schema=False)
async def deprecated_database_health():
    return {"status": "healthy", "service": "database"}
