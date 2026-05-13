import structlog
import logging
import sys
from typing import Any

from logging.src.handlers.json_handler import JSONLogHandler
from logging.src.formatters.structured import StructuredFormatter


class LoggingManager:
    def __init__(self, service_name: str = "ai-qa-platform", log_level: str = "INFO"):
        self.service_name = service_name
        self.log_level = log_level.upper()
        self._configure()

    def _configure(self) -> None:
        structlog.configure(
            processors=[
                structlog.contextvars.merge_contextvars,
                structlog.stdlib.filter_by_level,
                structlog.stdlib.add_logger_name,
                structlog.stdlib.add_log_level,
                structlog.stdlib.PositionalArgumentsFormatter(),
                structlog.processors.TimeStamper(fmt="iso"),
                structlog.processors.StackInfoRenderer(),
                structlog.processors.format_exc_info,
                structlog.processors.UnicodeDecoder(),
                StructuredFormatter(),
            ],
            wrapper_class=structlog.stdlib.BoundLogger,
            context_class=dict,
            logger_factory=structlog.stdlib.LoggerFactory(),
            cache_logger_on_first_use=True,
        )

        root_logger = logging.getLogger()
        root_logger.setLevel(self.log_level)

        json_handler = JSONLogHandler()
        json_handler.setLevel(self.log_level)
        root_logger.addHandler(json_handler)

        stream_handler = logging.StreamHandler(sys.stdout)
        stream_handler.setLevel(self.log_level)
        root_logger.addHandler(stream_handler)

    def get_logger(self, name: str | None = None) -> structlog.stdlib.BoundLogger:
        return structlog.get_logger(name or self.service_name)


def get_logger(service: str = "ai-qa-platform") -> structlog.stdlib.BoundLogger:
    return structlog.get_logger(service)
