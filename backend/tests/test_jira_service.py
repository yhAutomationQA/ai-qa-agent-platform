import pytest
from unittest.mock import AsyncMock, patch

from app.schemas.jira import JiraAuth, JiraIssue, JiraIssueFields, JiraIssueType, JiraPriority, JiraStatus
from app.services.jira_service import JiraService
from app.core.exceptions import ValidationError


@pytest.fixture
def auth():
    return JiraAuth(
        base_url="https://test.atlassian.net",
        email="test@example.com",
        api_token="fake-token",
    )


@pytest.fixture
def service(auth: JiraAuth):
    return JiraService(auth=auth)


def make_story_issue(key: str = "PROJ-123", summary: str = "A story", desc: str = "As a user...") -> JiraIssue:
    return JiraIssue(
        id="1",
        key=key,
        fields=JiraIssueFields(
            summary=summary,
            description=desc,
            issuetype=JiraIssueType(name="Story"),
            priority=JiraPriority(name="Medium"),
            status=JiraStatus(name="In Progress", category="In Progress"),
            labels=["qa"],
        ),
    )


def make_bug_issue(key: str = "PROJ-456", summary: str = "A bug") -> JiraIssue:
    return JiraIssue(
        id="2",
        key=key,
        fields=JiraIssueFields(
            summary=summary,
            description="Steps to Reproduce:\n1. Click X\n2. See error\n\nExpected Result:\nIt works\n\nActual Result:\nIt crashes\n\nEnvironment:\nChrome 120",
            issuetype=JiraIssueType(name="Bug"),
            priority=JiraPriority(name="High"),
            status=JiraStatus(name="Open", category="To Do"),
            labels=["bug"],
        ),
    )


class TestJiraService:
    @pytest.mark.asyncio
    async def test_test_connection_success(self, service: JiraService):
        from app.schemas.jira import JiraUser
        mock_user = JiraUser(account_id="u1", display_name="Test User", email_address="test@test.com")
        with patch.object(service.client, "test_connection", new=AsyncMock(return_value=mock_user)):
            result = await service.test_connection()
            assert result.connected is True
            assert result.user.display_name == "Test User"

    @pytest.mark.asyncio
    async def test_test_connection_failure(self, service: JiraService):
        with patch.object(service.client, "test_connection", new=AsyncMock(side_effect=ConnectionError("Failed"))):
            result = await service.test_connection()
            assert result.connected is False
            assert result.error is not None

    @pytest.mark.asyncio
    async def test_get_user_story_success(self, service: JiraService):
        with patch.object(service.client, "get_issue", new=AsyncMock(return_value=make_story_issue())):
            with patch.object(service.client, "get_issue_comments", new=AsyncMock(return_value=[])):
                story = await service.get_user_story("PROJ-123")
                assert story.issue_key == "PROJ-123"
                assert story.summary == "A story"
                assert story.priority == "Medium"
                assert story.status == "In Progress"

    @pytest.mark.asyncio
    async def test_get_user_story_wrong_type_raises(self, service: JiraService):
        with patch.object(service.client, "get_issue", new=AsyncMock(return_value=make_bug_issue())):
            with pytest.raises(ValidationError, match="expected 'Story'"):
                await service.get_user_story("PROJ-456")

    @pytest.mark.asyncio
    async def test_get_bug_success(self, service: JiraService):
        with patch.object(service.client, "get_issue", new=AsyncMock(return_value=make_bug_issue())):
            with patch.object(service.client, "get_issue_comments", new=AsyncMock(return_value=[])):
                bug = await service.get_bug("PROJ-456")
                assert bug.issue_key == "PROJ-456"
                assert bug.summary == "A bug"
                assert bug.priority == "High"

    @pytest.mark.asyncio
    async def test_get_acceptance_criteria(self, service: JiraService):
        issue = make_story_issue(
            desc="AC:\n- User can login\n- User can logout"
        )
        with patch.object(service.client, "get_issue", new=AsyncMock(return_value=issue)):
            ac = await service.get_acceptance_criteria("PROJ-123")
            assert len(ac.criteria) > 0

    @pytest.mark.asyncio
    async def test_get_comments_delegates(self, service: JiraService):
        with patch.object(service.client, "get_issue_comments", new=AsyncMock(return_value=[])):
            comments = await service.get_comments("PROJ-123")
            assert comments == []

    @pytest.mark.asyncio
    async def test_get_issue_by_key_validates_format(self, service: JiraService):
        with pytest.raises(ValidationError):
            await service.get_issue_by_key_or_id("invalid-format")

    @pytest.mark.asyncio
    async def test_get_issue_by_key_valid_format(self, service: JiraService):
        with patch.object(service.client, "get_issue", new=AsyncMock(return_value=make_story_issue("VALID-1"))):
            issue = await service.get_issue_by_key_or_id("VALID-1")
            assert issue.key == "VALID-1"

    @pytest.mark.asyncio
    async def test_add_comment(self, service: JiraService):
        from app.schemas.jira import JiraComment
        mock_comment = JiraComment(id="500", body="test comment")
        with patch.object(service.client, "add_comment", new=AsyncMock(return_value=mock_comment)):
            comment = await service.add_comment("PROJ-123", "test comment")
            assert comment.id == "500"
            assert comment.body == "test comment"
