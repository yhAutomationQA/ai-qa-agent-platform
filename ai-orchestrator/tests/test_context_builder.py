import pytest

from ai_orchestrator.context.builder import ContextBuilder
from ai_orchestrator.exceptions import ContextBuildError


@pytest.fixture
def builder():
    return ContextBuilder()


class TestContextBuilder:
    def test_build_sync_basic(self, builder: ContextBuilder):
        result = builder.build_sync("The system shall allow users to login.")
        assert result["word_count"] == 7
        assert result["char_count"] == 38
        assert result["has_code_blocks"] is False
        assert result["domain"] == "general"

    def test_build_sync_with_code_blocks(self, builder: ContextBuilder):
        result = builder.build_sync("API endpoint: ```GET /api/users```")
        assert result["has_code_blocks"] is True

    def test_build_sync_empty(self, builder: ContextBuilder):
        result = builder.build_sync("")
        assert result["word_count"] == 0

    def test_merge_with_extra(self, builder: ContextBuilder):
        base = builder.build_sync("test requirement")
        merged = builder.merge("test requirement", {"domain": "web", "priority": "high"})
        assert merged["domain"] == "web"
        assert merged["priority"] == "high"
        assert merged["word_count"] == 2

    def test_sentence_counting(self, builder: ContextBuilder):
        result = builder.build_sync("First sentence. Second sentence! Third?")
        assert result["sentences"] == 3

    @pytest.mark.asyncio
    async def test_build_async_empty_raises(self, builder: ContextBuilder):
        with pytest.raises(ContextBuildError):
            await builder.build("")
