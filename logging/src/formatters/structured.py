import structlog
import sys


class StructuredFormatter:
    def __call__(self, logger: structlog.stdlib.BoundLogger, method_name: str, event_dict: dict) -> dict:
        if sys.stderr.isatty():
            return event_dict
        event_dict["timestamp"] = event_dict.pop("timestamp", None)
        return event_dict
