import pytest
from unittest.mock import AsyncMock, patch

from app.schemas.jira import JiraAuth
from app.services.jira_client import JiraClient


@pytest.fixture
def auth():
    return JiraAuth(
        base_url="https://test.atlassian.net",
        email="test@example.com",
        api_token="fake-token",
    )


@pytest.fixture
def client(auth: JiraAuth):
    return JiraClient(auth=auth)


class TestJiraClientAuth:
    def test_build_auth_header(self):
        header = JiraClient._build_auth_header("user@e.com", "token123")
        assert header.startswith("Basic ")

    def test_client_initialization(self, client: JiraClient):
        assert client.base_url == "https://test.atlassian.net"
        assert client._auth_header.startswith("Basic ")


class TestJiraClientParsing:
    def test_extract_description_string(self):
        result = JiraClient._extract_description("plain text")
        assert result == "plain text"

    def test_extract_description_structured(self):
        atlassian_doc = {
            "type": "doc",
            "version": 1,
            "content": [
                {
                    "type": "paragraph",
                    "content": [{"type": "text", "text": "Hello world"}],
                }
            ],
        }
        result = JiraClient._extract_description(atlassian_doc)
        assert "Hello world" in result

    def test_extract_description_none(self):
        assert JiraClient._extract_description(None) == ""

    def test_extract_description_with_bullet_list(self):
        atlassian_doc = {
            "type": "doc",
            "content": [
                {
                    "type": "bulletList",
                    "content": [
                        {
                            "type": "listItem",
                            "content": [
                                {
                                    "type": "paragraph",
                                    "content": [{"type": "text", "text": "Item one"}],
                                }
                            ],
                        },
                        {
                            "type": "listItem",
                            "content": [
                                {
                                    "type": "paragraph",
                                    "content": [{"type": "text", "text": "Item two"}],
                                }
                            ],
                        },
                    ],
                }
            ],
        }
        result = JiraClient._extract_description(atlassian_doc)
        assert "- Item one" in result
        assert "- Item two" in result

    def test_parse_issue_basic(self):
        data = {
            "id": "10001",
            "key": "TEST-123",
            "self": "https://test.atlassian.net/rest/api/3/issue/10001",
            "fields": {
                "summary": "Test issue",
                "description": None,
                "issuetype": {"id": "1", "name": "Story", "description": "A story", "subtask": False},
                "priority": {"id": "2", "name": "High", "iconUrl": ""},
                "status": {"id": "3", "name": "In Progress", "statusCategory": {"name": "In Progress"}},
                "labels": ["qa"],
                "created": "2024-01-01T00:00:00.000+0000",
                "updated": "2024-01-02T00:00:00.000+0000",
            },
        }
        issue = JiraClient._parse_issue(data)
        assert issue.key == "TEST-123"
        assert issue.fields.summary == "Test issue"
        assert issue.fields.issuetype.name == "Story"
        assert issue.fields.priority.name == "High"
        assert issue.fields.status.name == "In Progress"
        assert issue.fields.labels == ["qa"]


class TestJiraClientAsync:
    @pytest.mark.asyncio
    async def test_connection_success(self, client: JiraClient):
        with patch.object(client, "_request", new=AsyncMock(return_value={
            "accountId": "abc123",
            "displayName": "Test User",
            "emailAddress": "test@example.com",
            "active": True,
        })):
            user = await client.test_connection()
            assert user.display_name == "Test User"
            assert user.account_id == "abc123"

    @pytest.mark.asyncio
    async def test_get_issue(self, client: JiraClient):
        mock_data = {
            "id": "100",
            "key": "PROJ-1",
            "fields": {
                "summary": "Bug fix",
                "issuetype": {"name": "Bug"},
                "priority": {"name": "Medium"},
                "status": {"name": "Open", "statusCategory": {"name": "To Do"}},
                "labels": [],
            },
        }
        with patch.object(client, "_request", new=AsyncMock(return_value=mock_data)):
            issue = await client.get_issue("PROJ-1")
            assert issue.key == "PROJ-1"
            assert issue.fields.summary == "Bug fix"

    @pytest.mark.asyncio
    async def test_search_issues(self, client: JiraClient):
        mock_data = {
            "issues": [
                {"id": "1", "key": "PROJ-1", "fields": {"summary": "First", "issuetype": {"name": "Story"}, "priority": {"name": "High"}, "status": {"name": "Open", "statusCategory": {"name": "To Do"}}, "labels": []}},
                {"id": "2", "key": "PROJ-2", "fields": {"summary": "Second", "issuetype": {"name": "Bug"}, "priority": {"name": "Low"}, "status": {"name": "Closed", "statusCategory": {"name": "Done"}}, "labels": []}},
            ],
            "total": 2,
            "startAt": 0,
            "maxResults": 50,
        }
        with patch.object(client, "_request", new=AsyncMock(return_value=mock_data)):
            result = await client.search_issues("project=TEST")
            assert result.total == 2
            assert len(result.issues) == 2
            assert result.issues[0].key == "PROJ-1"

    @pytest.mark.asyncio
    async def test_get_comments(self, client: JiraClient):
        mock_data = {
            "comments": [
                {
                    "id": "101",
                    "author": {"accountId": "u1", "displayName": "Alice"},
                    "body": {"type": "doc", "version": 1, "content": [{"type": "paragraph", "content": [{"type": "text", "text": "Fixed in v2"}]}]},
                    "created": "2024-01-01T00:00:00.000+0000",
                }
            ]
        }
        with patch.object(client, "_request", new=AsyncMock(return_value=mock_data)):
            comments = await client.get_issue_comments("PROJ-1")
            assert len(comments) == 1
            assert comments[0].author.display_name == "Alice"

    @pytest.mark.asyncio
    async def test_get_project(self, client: JiraClient):
        mock_data = {
            "id": "100",
            "key": "TEST",
            "name": "Test Project",
            "description": "A test project",
            "lead": {"accountId": "u1", "displayName": "Lead User"},
            "avatarUrls": {"48x48": "https://avatar.url"},
        }
        with patch.object(client, "_request", new=AsyncMock(return_value=mock_data)):
            project = await client.get_project("TEST")
            assert project.key == "TEST"
            assert project.name == "Test Project"
            assert project.lead.display_name == "Lead User"

    @pytest.mark.asyncio
    async def test_close(self, client: JiraClient):
        await client.close()
