import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any

from app.execution.models import TestExecution, ExecutionArtifact


class ExecutionStorage:
    def __init__(self, base_dir: str = ".execution_artifacts"):
        self._base = Path(base_dir)
        self._base.mkdir(parents=True, exist_ok=True)

    def _run_dir(self, execution_id: str) -> Path:
        path = self._base / execution_id
        path.mkdir(parents=True, exist_ok=True)
        return path

    def save_screenshot(
        self,
        execution_id: str,
        screenshot_data: bytes,
        step_name: str = "screenshot",
    ) -> ExecutionArtifact:
        run_dir = self._run_dir(execution_id)
        filename = f"{step_name}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.png"
        filepath = run_dir / filename
        filepath.write_bytes(screenshot_data)
        return ExecutionArtifact(
            name=filename,
            path=str(filepath),
            type="screenshot",
            size_bytes=len(screenshot_data),
        )

    def save_log(self, execution_id: str, log_text: str, suffix: str = "execution") -> ExecutionArtifact:
        run_dir = self._run_dir(execution_id)
        filename = f"{suffix}.log"
        filepath = run_dir / filename
        filepath.write_text(log_text, encoding="utf-8")
        return ExecutionArtifact(
            name=filename,
            path=str(filepath),
            type="log",
            size_bytes=len(log_text.encode("utf-8")),
        )

    def save_report(
        self,
        execution_id: str,
        report_data: str | bytes,
        filename: str = "report.xml",
    ) -> ExecutionArtifact:
        run_dir = self._run_dir(execution_id)
        filepath = run_dir / filename
        if isinstance(report_data, str):
            filepath.write_text(report_data, encoding="utf-8")
        else:
            filepath.write_bytes(report_data)
        return ExecutionArtifact(
            name=filename,
            path=str(filepath),
            type="report",
        )

    def save_execution_result(
        self,
        execution_id: str,
        execution: TestExecution,
    ) -> ExecutionArtifact:
        run_dir = self._run_dir(execution_id)
        filename = "execution_result.json"
        filepath = run_dir / filename
        with open(filepath, "w") as f:
            json.dump(execution.model_dump(mode="json"), f, indent=2, default=str)
        return ExecutionArtifact(
            name=filename,
            path=str(filepath),
            type="other",
        )

    def save_artifact(
        self,
        execution_id: str,
        data: bytes | str,
        filename: str,
        artifact_type: str = "other",
    ) -> ExecutionArtifact:
        run_dir = self._run_dir(execution_id)
        filepath = run_dir / filename
        if isinstance(data, str):
            filepath.write_text(data, encoding="utf-8")
        else:
            filepath.write_bytes(data)
        return ExecutionArtifact(
            name=filename,
            path=str(filepath),
            type=artifact_type,
            size_bytes=len(data) if isinstance(data, bytes) else len(data.encode("utf-8")),
        )

    def list_artifacts(self, execution_id: str) -> list[ExecutionArtifact]:
        run_dir = self._run_dir(execution_id)
        if not run_dir.exists():
            return []
        artifacts: list[ExecutionArtifact] = []
        for f in run_dir.iterdir():
            if f.is_file():
                ext = f.suffix.lower()
                atype = self._infer_type(ext)
                artifacts.append(
                    ExecutionArtifact(
                        name=f.name,
                        path=str(f),
                        type=atype,
                        size_bytes=f.stat().st_size,
                    )
                )
        return artifacts

    def cleanup(self, execution_id: str) -> None:
        run_dir = self._run_dir(execution_id)
        if run_dir.exists():
            shutil.rmtree(run_dir)

    @staticmethod
    def _infer_type(ext: str) -> str:
        mapping = {
            ".png": "screenshot",
            ".jpg": "screenshot",
            ".jpeg": "screenshot",
            ".log": "log",
            ".xml": "report",
            ".json": "report",
            ".html": "report",
            ".mp4": "video",
            ".webm": "video",
            ".zip": "trace",
        }
        return mapping.get(ext, "other")
