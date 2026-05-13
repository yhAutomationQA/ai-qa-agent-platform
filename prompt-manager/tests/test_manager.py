import pytest
import tempfile
from pathlib import Path

from prompt_manager.src.main import PromptManager


@pytest.fixture
def manager():
    with tempfile.TemporaryDirectory() as tmpdir:
        yield PromptManager(templates_dir=tmpdir)


class TestPromptManager:
    def test_register_and_render(self, manager: PromptManager):
        manager.register("greeting", "Hello {{ name }}!")
        result = manager.render("greeting", name="QA Agent")
        assert result == "Hello QA Agent!"

    def test_list_templates(self, manager: PromptManager):
        manager.register("test1", "template 1")
        manager.register("test2", "template 2")
        templates = manager.list()
        assert "test1" in templates
        assert "test2" in templates

    def test_delete_template(self, manager: PromptManager):
        manager.register("temp", "to be deleted")
        assert "temp" in manager.list()
        manager.delete("temp")
        assert "temp" not in manager.list()

    def test_missing_template_raises(self, manager: PromptManager):
        with pytest.raises(FileNotFoundError):
            manager.render("nonexistent")
