import logging
import json
from datetime import datetime


class JSONLogHandler(logging.Handler):
    def __init__(self):
        super().__init__()

    def emit(self, record: logging.LogRecord) -> None:
        try:
            log_entry = {
                "timestamp": datetime.utcfromtimestamp(record.created).isoformat(),
                "level": record.levelname,
                "logger": record.name,
                "message": record.getMessage(),
                "module": record.module,
                "function": record.funcName,
                "line": record.lineno,
            }

            if record.exc_info and record.exc_info[0]:
                log_entry["exception"] = {
                    "type": record.exc_info[0].__name__,
                    "message": str(record.exc_info[1]),
                }

            if hasattr(record, "extra"):
                log_entry["extra"] = record.extra

            print(json.dumps(log_entry, default=str), flush=True)
        except Exception:
            self.handleError(record)
