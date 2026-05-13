from typing import Annotated

from fastapi import APIRouter, Depends, Header, Query

from app.schemas.jira import (
    JiraAuth,
    JiraIssue,
    JiraComment,
    UserStory,
    BugReport,
    JiraAcceptanceCriteria,
    JiraConnectionTestResult,
    JiraSearchResult,
    JiraProject,
)
from app.services.jira_service import JiraService

router = APIRouter()


async def get_jira_service(
    x_jira_url: Annotated[str, Header(description="Jira instance base URL")],
    x_jira_email: Annotated[str, Header(description="Atlassian account email")],
    x_jira_token: Annotated[str, Header(description="Atlassian API token")],
) -> JiraService:
    auth = JiraAuth(base_url=x_jira_url, email=x_jira_email, api_token=x_jira_token)
    return JiraService(auth=auth)


@router.get("/connection/test", response_model=JiraConnectionTestResult)
async def test_connection(
    service: JiraService = Depends(get_jira_service),
):
    result = await service.test_connection()
    return result


@router.get("/projects", response_model=list[JiraProject])
async def list_projects(
    service: JiraService = Depends(get_jira_service),
):
    projects = await service.list_projects()
    return projects


@router.get("/projects/{project_key}", response_model=JiraProject)
async def get_project(
    project_key: str,
    service: JiraService = Depends(get_jira_service),
):
    return await service.get_project(project_key)


@router.get("/issues/{issue_key}", response_model=JiraIssue)
async def get_issue(
    issue_key: str,
    service: JiraService = Depends(get_jira_service),
):
    return await service.get_issue(issue_key)


@router.get("/issues/{issue_key}/user-story", response_model=UserStory)
async def get_user_story(
    issue_key: str,
    service: JiraService = Depends(get_jira_service),
):
    return await service.get_user_story(issue_key)


@router.get("/issues/{issue_key}/bug", response_model=BugReport)
async def get_bug(
    issue_key: str,
    service: JiraService = Depends(get_jira_service),
):
    return await service.get_bug(issue_key)


@router.get("/issues/{issue_key}/acceptance-criteria", response_model=JiraAcceptanceCriteria)
async def get_acceptance_criteria(
    issue_key: str,
    service: JiraService = Depends(get_jira_service),
):
    return await service.get_acceptance_criteria(issue_key)


@router.get("/issues/{issue_key}/comments", response_model=list[JiraComment])
async def get_comments(
    issue_key: str,
    service: JiraService = Depends(get_jira_service),
):
    return await service.get_comments(issue_key)


@router.post("/issues/{issue_key}/comments", response_model=JiraComment, status_code=201)
async def add_comment(
    issue_key: str,
    body: str = Query(..., description="Comment body text"),
    service: JiraService = Depends(get_jira_service),
):
    return await service.add_comment(issue_key, body)


@router.get("/search/stories", response_model=JiraSearchResult)
async def search_stories(
    project_key: str = Query(..., description="Jira project key"),
    jql_filter: str = Query("", description="Additional JQL filter"),
    max_results: int = Query(50, ge=1, le=200),
    service: JiraService = Depends(get_jira_service),
):
    return await service.search_stories(
        project_key=project_key,
        jql_filter=jql_filter,
        max_results=max_results,
    )


@router.get("/search/bugs", response_model=JiraSearchResult)
async def search_bugs(
    project_key: str = Query(..., description="Jira project key"),
    jql_filter: str = Query("", description="Additional JQL filter"),
    max_results: int = Query(50, ge=1, le=200),
    service: JiraService = Depends(get_jira_service),
):
    return await service.search_bugs(
        project_key=project_key,
        jql_filter=jql_filter,
        max_results=max_results,
    )
