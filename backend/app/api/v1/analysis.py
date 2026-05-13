from typing import Annotated

from fastapi import APIRouter, Depends, Header, Query

from app.schemas.jira import JiraAuth
from app.services.jira_service import JiraService
from agents.src.requirement_analysis.agent import RequirementAnalysisAgent
from agents.src.requirement_analysis.models import RequirementAnalysisOutput

router = APIRouter()


async def get_jira_service(
    x_jira_url: Annotated[str, Header(description="Jira instance base URL")],
    x_jira_email: Annotated[str, Header(description="Atlassian account email")],
    x_jira_token: Annotated[str, Header(description="Atlassian API token")],
) -> JiraService:
    auth = JiraAuth(base_url=x_jira_url, email=x_jira_email, api_token=x_jira_token)
    return JiraService(auth=auth)


@router.get("/requirements/{issue_key}", response_model=RequirementAnalysisOutput)
async def analyze_requirements(
    issue_key: str,
    include_comments: bool = Query(True, description="Include Jira comments in analysis"),
    service: JiraService = Depends(get_jira_service),
):
    issue = await service.get_issue(issue_key)
    f = issue.fields

    ac = await service.get_acceptance_criteria(issue_key)
    comments = await service.get_comments(issue_key) if include_comments else []

    task = {
        "issue_key": issue.key,
        "summary": f.summary,
        "description": f.description or "",
        "acceptance_criteria": ac.criteria,
        "comments": [
            {
                "author": {"displayName": c.author.display_name if c.author else ""},
                "body": c.body,
                "created": str(c.created) if c.created else "",
            }
            for c in comments
        ],
        "labels": f.labels,
        "priority": f.priority.name if f.priority else "",
        "issue_type": f.issuetype.name.lower() if f.issuetype else "story",
    }

    agent = RequirementAnalysisAgent()
    result = await agent.run(task)

    if result.status == "error":
        from fastapi import HTTPException
        raise HTTPException(status_code=500, detail=result.error)

    output = RequirementAnalysisOutput(**result.data)
    return output


@router.post("/requirements/from-text", response_model=RequirementAnalysisOutput)
async def analyze_requirements_from_text(
    summary: str = Query(..., description="Requirement summary"),
    description: str = Query("", description="Requirement description"),
    acceptance_criteria: str = Query("", description="Comma-separated acceptance criteria"),
):
    ac_list = [ac.strip() for ac in acceptance_criteria.split(",") if ac.strip()]

    task = {
        "issue_key": "MANUAL",
        "summary": summary,
        "description": description,
        "acceptance_criteria": ac_list,
        "comments": [],
        "labels": [],
        "priority": "",
    }

    agent = RequirementAnalysisAgent()
    result = await agent.run(task)

    if result.status == "error":
        from fastapi import HTTPException
        raise HTTPException(status_code=500, detail=result.error)

    output = RequirementAnalysisOutput(**result.data)
    return output
