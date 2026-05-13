import asyncio
import structlog
from typing import Callable, Any
from functools import wraps

from ai_orchestrator.exceptions import RateLimitError, AIServiceError
from ai_orchestrator.config import ai_config

logger = structlog.get_logger()


class RetryHandler:
    def __init__(
        self,
        max_attempts: int | None = None,
        backoff_factor: float | None = None,
        min_wait: float | None = None,
        max_wait: float | None = None,
    ):
        self.max_attempts = max_attempts or ai_config.LLM_RETRY_MAX_ATTEMPTS
        self.backoff_factor = backoff_factor or ai_config.LLM_RETRY_BACKOFF_FACTOR
        self.min_wait = min_wait or ai_config.LLM_RETRY_MIN_WAIT
        self.max_wait = max_wait or ai_config.LLM_RETRY_MAX_WAIT

    async def execute(
        self,
        func: Callable[..., Any],
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        last_exception: Exception | None = None

        for attempt in range(1, self.max_attempts + 1):
            try:
                return await func(*args, **kwargs)
            except RateLimitError as e:
                last_exception = e
                wait = e.retry_after or self._backoff(attempt)
                logger.warning(
                    "rate_limit_hit",
                    attempt=attempt,
                    max_attempts=self.max_attempts,
                    wait_seconds=round(wait, 2),
                )
                await asyncio.sleep(wait)
            except (ConnectionError, TimeoutError, AIServiceError) as e:
                last_exception = e
                if attempt == self.max_attempts:
                    logger.error(
                        "retry_exhausted",
                        error=str(e),
                        attempt=attempt,
                    )
                    raise
                wait = self._backoff(attempt)
                logger.warning(
                    "retry_attempt",
                    attempt=attempt,
                    max_attempts=self.max_attempts,
                    wait_seconds=round(wait, 2),
                    error=str(e),
                )
                await asyncio.sleep(wait)
            except Exception as e:
                logger.error("unexpected_error_no_retry", error=str(e))
                raise

        raise last_exception or AIServiceError("Retry handler exhausted with no exception")

    def _backoff(self, attempt: int) -> float:
        wait = self.min_wait * (self.backoff_factor ** (attempt - 1))
        return min(wait, self.max_wait)
