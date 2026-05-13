import pytest
import tempfile
from pathlib import Path

from ai_orchestrator.prompts.manager import PromptManager
from ai_orchestrator.exceptions import PromptTemplateError


@pytest.fixture
def manager():
    with tempfile.TemporaryDirectory() as tmpdir:
        yield PromptManager(template_dir=tmpdir)


class TestPromptManager:
    def test_register_and_render(self, manager: PromptManager):
        manager.register("greeting", "Hello {{ name }}!")
        result = manager.render("greeting", name="QA Agent")
        assert result == "Hello QA Agent!"

    def test_render_with_complex_variables(self, manager: PromptManager):
        manager.register("test", "Items: {{ items | join(', ') }}")
        result = manager.render("test", items=["a", "b", "c"])
        assert result == "Items: a, b, c"

    def test_list_templates(self, manager: PromptManager):
        manager.register("alpha", "content a")
        manager.register("beta", "content b")
        templates = manager.list_templates()
        assert templates == ["alpha", "beta"]

    def test_delete_template_does_not_exist(self, manager: PromptManager):
        with pytest.raises(PromptTemplateError):
            manager.render("nonexistent")

    def test_render_with_missing_variable(self, manager: PromptManager):
        from ai_orchestrator.prompts.manager import PromptTemplateError
        manager.register("needs_var", "Value: {{ var }}")
        result = manager.render("needs_var")
        assert result == "Value: "

    def test_get_template_content(self, manager: PromptManager):
        manager.register("sample", "template body")
        content = manager.get("sample")
        assert content == "template body"

    def test_render_uses_cache(self, manager: PromptManager):
        manager.register("cached", "original")
        manager.render("cached")
        manager.register("cached", "modified")
        result = manager.render("cached")
        assert result == "modified"
