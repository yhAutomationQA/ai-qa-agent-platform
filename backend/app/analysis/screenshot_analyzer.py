from pathlib import Path

from app.analysis.models import AnalysisInput


class ScreenshotAnalyzer:
    def __init__(self, ai_client=None):
        self._ai_client = ai_client

    async def analyze(self, input_data: AnalysisInput) -> dict | None:
        if not input_data.screenshot_path:
            return None

        path = Path(input_data.screenshot_path)
        if not path.exists():
            return None

        file_size = path.stat().st_size
        if file_size > 5_000_000:
            return {
                "note": "Screenshot too large for analysis",
                "size_bytes": file_size,
            }

        if self._ai_client and self._has_vision_capability():
            return await self._analyze_with_ai(path, input_data)

        return {
            "note": "Screenshot available but AI analysis not configured",
            "path": input_data.screenshot_path,
            "size_bytes": file_size,
        }

    async def _analyze_with_ai(self, path: Path, input_data: AnalysisInput) -> dict:
        try:
            import base64

            with open(path, "rb") as f:
                b64_data = base64.b64encode(f.read()).decode("utf-8")

            from app.analysis.prompts import SCREENSHOT_SYSTEM_PROMPT

            prompt = (
                f"Analyze this screenshot from a failed test.\n"
                f"Test: {input_data.test_name}\n"
                f"Error: {input_data.error_message}\n\n"
                f"Describe what you see and what might have caused the failure."
            )

            response = await self._ai_client.generate(
                prompt=prompt,
                system_prompt=SCREENSHOT_SYSTEM_PROMPT,
            )

            return {
                "analysis": response.content,
                "path": str(path),
            }

        except Exception as e:
            return {
                "note": f"Screenshot AI analysis failed: {e}",
                "path": str(path),
            }

    def _has_vision_capability(self) -> bool:
        if self._ai_client is None:
            return False
        model = getattr(self._ai_client, "model_name", "") or ""
        return "vision" in model.lower() or "gpt-4" in model.lower()
