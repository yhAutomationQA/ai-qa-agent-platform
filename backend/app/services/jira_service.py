import structlog
import re
from typing import Any

from app.schemas.jira import (
    JiraAuth,
    JiraIssue,
    JiraComment,
    UserStory,
    BugReport,
    JiraAcceptanceCriteria,
    JiraConnectionTestResult,
    JiraProject,
    JiraSearchResult,
    JiraUser,
)
from app.services.jira_client import JiraClient
from app.core.exceptions import NotFoundError, ValidationError

logger = structlog.get_logger()


class JiraService:
    def __init__(self, auth: JiraAuth):
        self.client = JiraClient(auth=auth)

    async def test_connection(self) -> JiraConnectionTestResult:
        try:
            user = await self.client.test_connection()
            return JiraConnectionTestResult(connected=True, user=user)
        except Exception as e:
            logger.error("jira_connection_failed", error=str(e))
            return JiraConnectionTestResult(connected=False, error=str(e))

    async def get_issue(self, issue_key: str) -> JiraIssue:
        result = await self.client.get_issue(issue_key)
        if not result.key:
            raise NotFoundError("JiraIssue", issue_key)
        return result

    async def get_user_story(self, issue_key: str) -> UserStory:
        issue = await self.get_issue(issue_key)
        self._assert_type(issue, "Story")

        criteria = await self._parse_acceptance_criteria(issue)
        comments = await self.client.get_issue_comments(issue_key)
        f = issue.fields

        return UserStory(
            issue_key=issue.key,
            summary=f.summary,
            description=f.description or "",
            acceptance_criteria=criteria,
            comments=comments,
            labels=f.labels,
            priority=f.priority.name if f.priority else "",
            status=f.status.name if f.status else "",
            assignee=f.assignee.display_name if f.assignee else "",
            reporter=f.reporter.display_name if f.reporter else "",
            created=f.created,
            updated=f.updated,
        )

    async def get_bug(self, issue_key: str) -> BugReport:
        issue = await self.get_issue(issue_key)
        self._assert_type(issue, "Bug")

        comments = await self.client.get_issue_comments(issue_key)
        f = issue.fields
        steps, expected, actual, environment = self._parse_bug_fields(f.description or "")

        return BugReport(
            issue_key=issue.key,
            summary=f.summary,
            description=f.description or "",
            environment=environment,
            steps_to_reproduce=steps,
            expected_result=expected,
            actual_result=actual,
            severity=f.customfield_10000 or "",
            priority=f.priority.name if f.priority else "",
            status=f.status.name if f.status else "",
            assignee=f.assignee.display_name if f.assignee else "",
            reporter=f.reporter.display_name if f.reporter else "",
            labels=f.labels,
            comments=comments,
            affected_versions=[v for v in f.fix_versions],
            created=f.created,
            updated=f.updated,
        )

    async def get_acceptance_criteria(self, issue_key: str) -> JiraAcceptanceCriteria:
        issue = await self.get_issue(issue_key)
        criteria = await self._parse_acceptance_criteria(issue)
        return JiraAcceptanceCriteria(
            raw_text=issue.fields.description or "",
            criteria=criteria,
            source_issue_key=issue.key,
        )

    async def get_comments(self, issue_key: str) -> list[JiraComment]:
        return await self.client.get_issue_comments(issue_key)

    async def search_stories(
        self,
        project_key: str,
        jql_filter: str = "",
        max_results: int = 50,
    ) -> JiraSearchResult:
        jql = f'project={project_key} AND issuetype=Story'
        if jql_filter:
            jql += f" AND {jql_filter}"
        return await self.client.search_issues(jql, max_results=max_results)

    async def search_bugs(
        self,
        project_key: str,
        jql_filter: str = "",
        max_results: int = 50,
    ) -> JiraSearchResult:
        jql = f'project={project_key} AND issuetype=Bug'
        if jql_filter:
            jql += f" AND {jql_filter}"
        return await self.client.search_issues(jql, max_results=max_results)

    async def get_project(self, project_key: str) -> JiraProject:
        return await self.client.get_project(project_key)

    async def list_projects(self) -> list[JiraProject]:
        return await self.client.list_projects()

    async def add_comment(self, issue_key: str, body: str) -> JiraComment:
        return await self.client.add_comment(issue_key, body)

    async def get_issue_by_key_or_id(self, identifier: str) -> JiraIssue:
        if not re.match(r"^[A-Z]+-\d+$", identifier):
            raise ValidationError(f"Invalid issue key format: {identifier}")
        return await self.get_issue(identifier)

    async def close(self) -> None:
        await self.client.close()

    @staticmethod
    def _assert_type(issue: JiraIssue, expected: str) -> None:
        actual = issue.fields.issuetype.name if issue.fields.issuetype else ""
        if actual.lower() != expected.lower():
            raise ValidationError(
                f"Issue {issue.key} is type '{actual}', expected '{expected}'"
            )

    @staticmethod
    async def _parse_acceptance_criteria(issue: JiraIssue) -> list[str]:
        desc = issue.fields.description or ""

        criteria_list = re.findall(
            r"(?:AC|Acceptance Criteria|Gherkin)[:\s]*(.*?)(?=\n\n|\Z)",
            desc,
            re.IGNORECASE | re.DOTALL,
        )

        if not criteria_list:
            lines = desc.strip().split("\n")
            criteria_list = [
                line.strip().lstrip("*•-").strip()
                for line in lines
                if line.strip()
                and not line.strip().startswith(("Given", "When", "Then", "And", "Feature:", "Scenario:"))
            ][:1]

        result = []
        for block in criteria_list:
            items = re.split(r"\n\s*[\*\-•]\s*", block.strip())
            for item in items:
                cleaned = item.strip().strip("*•-").strip()
                if cleaned and len(cleaned) > 5:
                    result.append(cleaned)

        return result

    @staticmethod
    def _parse_bug_fields(description: str) -> tuple[list[str], str, str, str]:
        steps: list[str] = []
        expected = ""
        actual = ""
        environment = ""

        sections = re.split(r"\n(?=###|\*\*|Steps to|Expected|Actual|Environment)", description)

        for section in sections:
            lower = section.lower().strip()
            if lower.startswith(("steps to reproduce", "**steps to reproduce")):
                steps = [
                    line.strip().lstrip("*•-1234567890.)").strip()
                    for line in section.split("\n")[1:]
                    if line.strip()
                ]
            elif lower.startswith(("expected result", "**expected result", "expected behavior", "**expected behavior")):
                expected = "\n".join(line.strip() for line in section.split("\n")[1:] if line.strip())
            elif lower.startswith(("actual result", "**actual result", "actual behavior", "**actual behavior")):
                actual = "\n".join(line.strip() for line in section.split("\n")[1:] if line.strip())
            elif lower.startswith(("environment", "**environment")):
                environment = "\n".join(line.strip() for line in section.split("\n")[1:] if line.strip())

        return steps, expected, actual, environment
