from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
async def health_check():
    return {"status": "healthy", "service": "ai-qa-platform", "version": "1.0.0"}


@router.get("/health/database")
async def database_health():
    return {"status": "healthy", "service": "database"}
