import pytest
import structlog

from logging.src.main import LoggingManager


@pytest.fixture
def log_manager():
    return LoggingManager(service_name="test-service", log_level="DEBUG")


def test_logger_creation(log_manager: LoggingManager):
    logger = log_manager.get_logger("test-logger")
    assert logger is not None
    assert isinstance(logger, structlog.stdlib.BoundLogger)


def test_logger_emits_without_error(log_manager: LoggingManager):
    logger = log_manager.get_logger("test-logger")
    logger.info("test message", extra_field="value")
    logger.error("error message")
    logger.debug("debug message")
