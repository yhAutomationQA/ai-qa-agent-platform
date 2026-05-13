from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class JiraAuth(BaseModel):
    base_url: str = Field(..., description="Jira instance base URL, e.g. https://your-domain.atlassian.net")
    email: str = Field(..., description="Atlassian account email")
    api_token: str = Field(..., description="Atlassian API token")


class JiraIssueType(BaseModel):
    id: str = ""
    name: str = ""
    description: str = ""
    subtask: bool = False


class JiraPriority(BaseModel):
    id: str = ""
    name: str = ""
    icon_url: str = ""


class JiraStatus(BaseModel):
    id: str = ""
    name: str = ""
    category: str = ""


class JiraUser(BaseModel):
    account_id: str = ""
    display_name: str = ""
    email_address: str = ""
    active: bool = True


class JiraIssueFields(BaseModel):
    summary: str = ""
    description: str | None = None
    issuetype: JiraIssueType | None = None
    priority: JiraPriority | None = None
    status: JiraStatus | None = None
    assignee: JiraUser | None = None
    reporter: JiraUser | None = None
    created: datetime | None = None
    updated: datetime | None = None
    labels: list[str] = Field(default_factory=list)
    fix_versions: list[str] = Field(default_factory=list, alias="fixVersions")
    customfield_10000: Any = None


class JiraIssue(BaseModel):
    id: str = ""
    key: str = ""
    self_url: str = ""
    fields: JiraIssueFields = Field(default_factory=JiraIssueFields)

    model_config = {"populate_by_name": True}


class JiraComment(BaseModel):
    id: str = ""
    author: JiraUser | None = None
    body: str = ""
    created: datetime | None = None
    updated: datetime | None = None


class JiraAcceptanceCriteria(BaseModel):
    raw_text: str = ""
    criteria: list[str] = Field(default_factory=list)
    source_issue_key: str = ""


class UserStory(BaseModel):
    issue_key: str = ""
    summary: str = ""
    description: str = ""
    acceptance_criteria: list[str] = Field(default_factory=list)
    comments: list[JiraComment] = Field(default_factory=list)
    labels: list[str] = Field(default_factory=list)
    priority: str = ""
    status: str = ""
    assignee: str = ""
    reporter: str = ""
    created: datetime | None = None
    updated: datetime | None = None


class BugReport(BaseModel):
    issue_key: str = ""
    summary: str = ""
    description: str = ""
    environment: str = ""
    steps_to_reproduce: list[str] = Field(default_factory=list)
    expected_result: str = ""
    actual_result: str = ""
    severity: str = ""
    priority: str = ""
    status: str = ""
    assignee: str = ""
    reporter: str = ""
    labels: list[str] = Field(default_factory=list)
    comments: list[JiraComment] = Field(default_factory=list)
    affected_versions: list[str] = Field(default_factory=list)
    created: datetime | None = None
    updated: datetime | None = None


class JiraSearchResult(BaseModel):
    issues: list[JiraIssue] = Field(default_factory=list)
    total: int = 0
    start_at: int = 0
    max_results: int = 50


class JiraProject(BaseModel):
    id: str = ""
    key: str = ""
    name: str = ""
    description: str = ""
    lead: JiraUser | None = None
    avatar_url: str = ""


class JiraWebhookPayload(BaseModel):
    webhook_event: str = ""
    issue: JiraIssue | None = None
    comment: JiraComment | None = None
    changelog: dict[str, Any] = Field(default_factory=dict)


class JiraConnectionTestResult(BaseModel):
    connected: bool = False
    user: JiraUser | None = None
    error: str | None = None
