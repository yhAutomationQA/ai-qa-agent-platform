from fastapi import APIRouter

from app.api.v1 import agents, tests, runs, prompts, configs, jira, analysis

router = APIRouter()

router.include_router(agents.router, prefix="/agents", tags=["agents"])
router.include_router(tests.router, prefix="/tests", tags=["tests"])
router.include_router(runs.router, prefix="/runs", tags=["runs"])
router.include_router(prompts.router, prefix="/prompts", tags=["prompts"])
router.include_router(configs.router, prefix="/configs", tags=["configs"])
router.include_router(jira.router, prefix="/jira", tags=["jira"])
router.include_router(analysis.router, prefix="/analysis", tags=["analysis"])
