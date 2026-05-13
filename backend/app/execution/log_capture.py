import asyncio
from datetime import datetime
from typing import AsyncIterator

from app.execution.models import ExecutionLog


class LogCapture:
    def __init__(self, max_bytes: int = 10_485_760):
        self._logs: list[ExecutionLog] = []
        self._max_bytes = max_bytes
        self._current_bytes = 0

    @property
    def logs(self) -> list[ExecutionLog]:
        return list(self._logs)

    @property
    def raw_text(self) -> str:
        return "\n".join(f"[{log.level}] {log.message}" for log in self._logs)

    def add(self, message: str, level: str = "INFO", source: str = "system") -> None:
        entry_size = len(message.encode("utf-8"))
        if self._current_bytes + entry_size > self._max_bytes:
            return
        self._logs.append(
            ExecutionLog(
                timestamp=datetime.utcnow(),
                level=level,
                source=source,
                message=message,
            )
        )
        self._current_bytes += entry_size

    def add_separator(self, char: str = "-", count: int = 60) -> None:
        self.add(char * count, level="INFO", source="system")

    async def capture_stream(
        self,
        stream: asyncio.StreamReader,
        source: str = "stdout",
        level: str = "INFO",
    ) -> None:
        while True:
            line = await stream.readline()
            if not line:
                break
            decoded = line.decode("utf-8", errors="replace").rstrip("\n")
            if decoded:
                self.add(decoded, level=level, source=source)

    @staticmethod
    async def read_stream(stream: asyncio.StreamReader) -> AsyncIterator[str]:
        while True:
            line = await stream.readline()
            if not line:
                break
            yield line.decode("utf-8", errors="replace").rstrip("\n")

    def merge(self, other: "LogCapture") -> None:
        for log in other._logs:
            entry_size = len(log.message.encode("utf-8"))
            if self._current_bytes + entry_size > self._max_bytes:
                break
            self._logs.append(log)
            self._current_bytes += entry_size

    def clear(self) -> None:
        self._logs.clear()
        self._current_bytes = 0
