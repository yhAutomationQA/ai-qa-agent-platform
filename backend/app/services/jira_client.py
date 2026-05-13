import structlog
import base64
from typing import Any

import httpx

from app.core.exceptions import ServiceUnavailableError, AuthenticationError
from app.schemas.jira import (
    JiraAuth,
    JiraIssue,
    JiraIssueFields,
    JiraIssueType,
    JiraPriority,
    JiraStatus,
    JiraComment,
    JiraSearchResult,
    JiraProject,
    JiraUser,
)

logger = structlog.get_logger()


class JiraClient:
    def __init__(self, auth: JiraAuth, timeout: int = 30):
        self.base_url = auth.base_url.rstrip("/")
        self._auth_header = self._build_auth_header(auth.email, auth.api_token)
        self.timeout = timeout
        self._client: httpx.AsyncClient | None = None

    @staticmethod
    def _build_auth_header(email: str, api_token: str) -> str:
        credentials = f"{email}:{api_token}"
        encoded = base64.b64encode(credentials.encode()).decode()
        return f"Basic {encoded}"

    @property
    def client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                headers={
                    "Authorization": self._auth_header,
                    "Accept": "application/json",
                    "Content-Type": "application/json",
                },
                timeout=httpx.Timeout(self.timeout),
            )
        return self._client

    async def _request(
        self,
        method: str,
        path: str,
        params: dict[str, Any] | None = None,
        json_data: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        url = f"/rest/api/3/{path.lstrip('/')}"
        logger.debug("jira_request", method=method, url=url, params=params)

        try:
            response = await self.client.request(method, url, params=params, json=json_data)
        except httpx.ConnectError as e:
            raise ServiceUnavailableError(f"Jira at {self.base_url}") from e
        except httpx.TimeoutException as e:
            raise ServiceUnavailableError(f"Jira timed out at {self.base_url}") from e

        if response.status_code == 401:
            raise AuthenticationError("Invalid Jira credentials (email + API token)")
        if response.status_code == 403:
            raise AuthenticationError("Jira account lacks permission for this resource")
        if response.status_code == 404:
            return {}
        if response.status_code == 429:
            retry_after = response.headers.get("Retry-After", "5")
            logger.warning("jira_rate_limited", retry_after=retry_after)

        response.raise_for_status()
        return response.json()

    async def test_connection(self) -> JiraUser:
        data = await self._request("GET", "myself")
        return JiraUser(
            account_id=data.get("accountId", ""),
            display_name=data.get("displayName", ""),
            email_address=data.get("emailAddress", ""),
            active=data.get("active", True),
        )

    async def get_issue(self, issue_key: str) -> JiraIssue:
        data = await self._request("GET", f"issue/{issue_key}")
        return self._parse_issue(data)

    async def search_issues(
        self,
        jql: str,
        fields: list[str] | None = None,
        start_at: int = 0,
        max_results: int = 50,
    ) -> JiraSearchResult:
        params: dict[str, Any] = {
            "jql": jql,
            "startAt": start_at,
            "maxResults": max_results,
        }
        if fields:
            params["fields"] = ",".join(fields)

        data = await self._request("GET", "search", params=params)
        issues = [self._parse_issue(item) for item in data.get("issues", [])]

        return JiraSearchResult(
            issues=issues,
            total=data.get("total", 0),
            start_at=data.get("startAt", 0),
            max_results=data.get("maxResults", 50),
        )

    async def get_issue_comments(self, issue_key: str) -> list[JiraComment]:
        data = await self._request("GET", f"issue/{issue_key}/comment")
        comments = []
        for item in data.get("comments", []):
            author_data = item.get("author", {})
            comments.append(
                JiraComment(
                    id=item.get("id", ""),
                    author=JiraUser(
                        account_id=author_data.get("accountId", ""),
                        display_name=author_data.get("displayName", ""),
                        email_address=author_data.get("emailAddress", ""),
                    ),
                    body=item.get("body", {}).get("content", [{}])[0].get("content", [{}])[0]
                    .get("text", "")
                    if isinstance(item.get("body"), dict)
                    else str(item.get("body", "")),
                    created=item.get("created"),
                    updated=item.get("updated"),
                )
            )
        return comments

    async def get_project(self, project_key: str) -> JiraProject:
        data = await self._request("GET", f"project/{project_key}")
        lead_data = data.get("lead", {})
        return JiraProject(
            id=data.get("id", ""),
            key=data.get("key", ""),
            name=data.get("name", ""),
            description=data.get("description", "") or "",
            lead=JiraUser(
                account_id=lead_data.get("accountId", ""),
                display_name=lead_data.get("displayName", ""),
                email_address=lead_data.get("emailAddress", ""),
            ),
            avatar_url=data.get("avatarUrls", {}).get("48x48", ""),
        )

    async def list_projects(self) -> list[JiraProject]:
        data = await self._request("GET", "project")
        projects = []
        for item in data:
            lead_data = item.get("lead", {})
            projects.append(
                JiraProject(
                    id=item.get("id", ""),
                    key=item.get("key", ""),
                    name=item.get("name", ""),
                    description=item.get("description") or "",
                    lead=JiraUser(
                        account_id=lead_data.get("accountId", ""),
                        display_name=lead_data.get("displayName", ""),
                    ),
                )
            )
        return projects

    async def get_issue_transitions(self, issue_key: str) -> list[dict[str, Any]]:
        data = await self._request("GET", f"issue/{issue_key}/transitions")
        return data.get("transitions", [])

    async def add_comment(self, issue_key: str, body: str) -> JiraComment:
        payload = {"body": {"type": "doc", "version": 1, "content": [{"type": "paragraph", "content": [{"type": "text", "text": body}]}]}}
        data = await self._request("POST", f"issue/{issue_key}/comment", json_data=payload)
        return JiraComment(
            id=data.get("id", ""),
            author=JiraUser(
                account_id=data.get("author", {}).get("accountId", ""),
                display_name=data.get("author", {}).get("displayName", ""),
            ),
            body=body,
            created=data.get("created"),
        )

    @staticmethod
    def _parse_issue(data: dict[str, Any]) -> JiraIssue:
        raw = data.get("fields", {})
        it = raw.get("issuetype", {})
        pr = raw.get("priority", {})
        st = raw.get("status", {})
        ad = raw.get("assignee")
        rd = raw.get("reporter")

        fields_obj = JiraIssueFields(
            summary=raw.get("summary", ""),
            description=JiraClient._extract_description(raw.get("description")),
            issuetype=JiraIssueType(
                id=it.get("id", ""),
                name=it.get("name", ""),
                description=it.get("description", ""),
                subtask=it.get("subtask", False),
            ),
            priority=JiraPriority(
                id=pr.get("id", ""),
                name=pr.get("name", ""),
                icon_url=pr.get("iconUrl", ""),
            ),
            status=JiraStatus(
                id=st.get("id", ""),
                name=st.get("name", ""),
                category=st.get("statusCategory", {}).get("name", ""),
            ),
            assignee=JiraUser(
                account_id=ad.get("accountId", ""),
                display_name=ad.get("displayName", ""),
                email_address=ad.get("emailAddress", ""),
            ) if ad else None,
            reporter=JiraUser(
                account_id=rd.get("accountId", ""),
                display_name=rd.get("displayName", ""),
                email_address=rd.get("emailAddress", ""),
            ) if rd else None,
            created=raw.get("created"),
            updated=raw.get("updated"),
            labels=raw.get("labels", []),
        )

        return JiraIssue(
            id=data.get("id", ""),
            key=data.get("key", ""),
            self_url=data.get("self", ""),
            fields=fields_obj,
        )

    @staticmethod
    def _extract_description(desc: Any) -> str:
        if not desc:
            return ""
        if isinstance(desc, str):
            return desc
        try:
            text_parts = []
            content = desc.get("content", [])
            for block in content:
                block_type = block.get("type", "")
                if block_type == "paragraph":
                    for item in block.get("content", []):
                        if item.get("type") == "text":
                            text_parts.append(item.get("text", ""))
                        elif item.get("type") == "inlineCard":
                            text_parts.append(item.get("attrs", {}).get("url", ""))
                elif block_type == "bulletList":
                    for item in block.get("content", []):
                        for child in item.get("content", []):
                            for grandchild in child.get("content", []):
                                if grandchild.get("type") == "text":
                                    text_parts.append(f"- {grandchild.get('text', '')}")
            return "\n".join(text_parts)
        except (KeyError, IndexError, TypeError):
            return str(desc)

    async def close(self) -> None:
        if self._client:
            await self._client.aclose()
            self._client = None
