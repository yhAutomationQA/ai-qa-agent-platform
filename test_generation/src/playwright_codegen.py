from __future__ import annotations

import structlog
from typing import Any

from .models import GeneratedTestFile, TestGenerationInput
from .utils import clean_code_block, format_ts_code, sanitize_filename

logger = structlog.get_logger()

PAGE_OBJECT_TEMPLATE = """import {{ Page, Locator, expect }} from "@playwright/test";

export class {page_class_name} {{
  readonly page: Page;

  constructor(page: Page) {{
    this.page = page;
  }}

{locators}

{methods}
}}
"""

FIXTURE_TEMPLATE = """import {{ test as base, expect, Page }} from "@playwright/test";
import {{ {page_class_name} }} from "./{page_file}";

type Fixtures = {{
  {fixture_name}: {page_class_name};
}};

export const test = base.extend<Fixtures>({{
  {fixture_name}: async ({{ page }}, use) => {{
    await use(new {page_class_name}(page));
  }},
}});

export {{ expect }} from "@playwright/test";
"""

TEST_TEMPLATE = """import {{ test, expect }} from "@fixtures/{fixture_path}";
import {{ {data_imports} }} from "@data/users";

test.describe("{feature_name}", {{
  test.beforeEach(async ({{ {fixture_name} }}) => {{
    await {fixture_name}.goto();
  }});

{tests}
}});
"""


class PlaywrightCodeGenerator:
    def __init__(self, config: dict[str, Any] | None = None):
        self.config = config or {}

    def generate_all(
        self,
        feature_name: str,
        page_objects: list[dict[str, Any]],
        test_cases: list[dict[str, Any]],
    ) -> list[GeneratedTestFile]:
        """Generate a complete Playwright test suite from structured descriptions."""
        files: list[GeneratedTestFile] = []
        safe_name = sanitize_filename(feature_name)

        for po in page_objects:
            page_file = self._generate_page_object(po, safe_name)
            files.append(page_file)

            fixture_file = self._generate_fixture(po, safe_name)
            files.append(fixture_file)

        spec_file = self._generate_spec(feature_name, safe_name, test_cases, page_objects)
        files.append(spec_file)

        logger.info("playwright_files_generated", count=len(files), feature=feature_name)
        return files

    def generate_from_llm_output(
        self,
        input_data: TestGenerationInput,
        llm_output: dict[str, Any],
    ) -> list[GeneratedTestFile]:
        """Parse LLM output into generated test files."""
        files: list[GeneratedTestFile] = []
        safe_name = sanitize_filename(input_data.requirement_summary[:50])

        raw_code = llm_output.get("code", "")
        if raw_code:
            cleaned = clean_code_block(raw_code)
            formatted = format_ts_code(cleaned)
            files.append(
                GeneratedTestFile(
                    filename=f"tests/{safe_name}/{safe_name}.spec.ts",
                    code=formatted,
                    description=f"Playwright UI tests for: {input_data.requirement_summary[:80]}",
                )
            )

        raw_page = llm_output.get("page_object", "")
        if raw_page:
            cleaned = clean_code_block(raw_page)
            formatted = format_ts_code(cleaned)
            files.append(
                GeneratedTestFile(
                    filename=f"pages/{safe_name}.page.ts",
                    code=formatted,
                    description=f"Page Object Model for {safe_name} feature",
                )
            )

        return files

    def _generate_page_object(
        self,
        page_obj: dict[str, Any],
        safe_name: str,
    ) -> GeneratedTestFile:
        class_name = f"{page_obj.get('name', 'Feature')}Page"
        fixture_name = f"{page_obj.get('name', 'feature').lower()}Page"

        locator_lines = []
        for el in page_obj.get("elements", []):
            name = el.get("name", "element")
            selector = el.get("selector", f'[data-testid="{name}"]')
            locator_lines.append(f"  get {name}(): Locator {{")
            locator_lines.append(f"    return this.page.locator('{selector}');")
            locator_lines.append(f"  }}")

        method_lines = []
        for action in page_obj.get("actions", []):
            action_name = action.get("name", "doAction")
            steps = action.get("steps", [])
            method_lines.append(f"  async {action_name}(): Promise<void> {{")
            for step in steps:
                method_lines.append(f"    await this.{step};")
            method_lines.append(f"  }}")

        code = PAGE_OBJECT_TEMPLATE.format(
            page_class_name=class_name,
            locators="\n\n".join(locator_lines) if locator_lines else "  // locators",
            methods="\n\n".join(method_lines) if method_lines else "  // methods",
        )

        return GeneratedTestFile(
            filename=f"pages/{safe_name}.page.ts",
            code=format_ts_code(code),
            description=f"Page Object: {class_name}",
        )

    def _generate_fixture(
        self,
        page_obj: dict[str, Any],
        safe_name: str,
    ) -> GeneratedTestFile:
        class_name = f"{page_obj.get('name', 'Feature')}Page"
        fixture_name = f"{page_obj.get('name', 'feature').lower()}Page"

        code = FIXTURE_TEMPLATE.format(
            page_class_name=class_name,
            page_file=safe_name,
            fixture_name=fixture_name,
        )

        return GeneratedTestFile(
            filename=f"fixtures/{safe_name}.fixture.ts",
            code=format_ts_code(code),
            description=f"Fixture: {fixture_name}",
        )

    def _generate_spec(
        self,
        feature_name: str,
        safe_name: str,
        test_cases: list[dict[str, Any]],
        page_objects: list[dict[str, Any]],
    ) -> GeneratedTestFile:
        fixture_name = "base"
        fixture_path = "base"

        data_imports_parts = set()
        data_imports = ""

        test_lines = []
        for tc in test_cases:
            name = tc.get("name", "should behave as expected")
            steps = tc.get("steps", [])
            test_lines.append(f'  test("{name}", async ({{ {fixture_name} }}) => {{')
            for step in steps:
                test_lines.append(f"    await {step};")
            test_lines.append("  });")
            test_lines.append("")

        code = TEST_TEMPLATE.format(
            fixture_path=fixture_path,
            data_imports=data_imports or " ",
            feature_name=feature_name,
            fixture_name=fixture_name,
            tests="\n".join(test_lines).rstrip(),
        )

        return GeneratedTestFile(
            filename=f"tests/{safe_name}/{safe_name}.spec.ts",
            code=format_ts_code(code),
            description=f"Test spec: {feature_name}",
        )
