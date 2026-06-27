"""Retry decorator with exponential backoff for external service calls.

Gold Tier — Error Recovery (FR-016, FR-017).
Wraps external calls with configurable retries and backoff.
Updates service health on each attempt.
"""

import functools
import time
import logging

logger = logging.getLogger(__name__)


class RetryExhausted(Exception):
    """Raised when all retry attempts are exhausted."""

    def __init__(self, original_exception, attempts):
        self.original_exception = original_exception
        self.attempts = attempts
        super().__init__(
            f"All {attempts} retry attempts exhausted. Last error: {original_exception}"
        )


def retry(
    max_attempts=3,
    backoff_base=1,
    backoff_factor=2,
    retryable_exceptions=(ConnectionError, TimeoutError, OSError),
    on_retry=None,
    on_failure=None,
):
    """Decorator that retries a function with exponential backoff.

    Args:
        max_attempts: Maximum number of attempts (including first try).
        backoff_base: Initial delay in seconds before first retry.
        backoff_factor: Multiplier for each subsequent delay.
        retryable_exceptions: Tuple of exception types to retry on.
        on_retry: Optional callback(attempt, exception, delay) called before each retry.
        on_failure: Optional callback(exception, attempts) called when all retries exhausted.

    Delays: backoff_base * (backoff_factor ** attempt_index)
    Example with defaults: 1s, 2s, 4s
    """

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None

            for attempt in range(max_attempts):
                try:
                    result = func(*args, **kwargs)
                    return result
                except retryable_exceptions as e:
                    last_exception = e
                    if attempt < max_attempts - 1:
                        delay = backoff_base * (backoff_factor ** attempt)
                        logger.warning(
                            "Attempt %d/%d failed for %s: %s. Retrying in %.1fs...",
                            attempt + 1,
                            max_attempts,
                            func.__name__,
                            str(e),
                            delay,
                        )
                        if on_retry:
                            on_retry(attempt + 1, e, delay)
                        time.sleep(delay)
                    else:
                        logger.error(
                            "All %d attempts exhausted for %s: %s",
                            max_attempts,
                            func.__name__,
                            str(e),
                        )
                        if on_failure:
                            on_failure(e, max_attempts)

            raise RetryExhausted(last_exception, max_attempts)

        return wrapper

    return decorator


def retry_with_health(
    service_name,
    health_tracker=None,
    max_attempts=3,
    backoff_base=1,
    backoff_factor=2,
    retryable_exceptions=(ConnectionError, TimeoutError, OSError),
):
    """Retry decorator that also updates service health status.

    Args:
        service_name: Name of the service for health tracking.
        health_tracker: ServiceHealthTracker instance (optional).
        Other args: Same as retry().
    """

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            def _on_failure(exc, attempts):
                if health_tracker:
                    health_tracker.update_health(service_name, success=False, error=str(exc))

            try:
                result = retry(
                    max_attempts=max_attempts,
                    backoff_base=backoff_base,
                    backoff_factor=backoff_factor,
                    retryable_exceptions=retryable_exceptions,
                    on_failure=_on_failure,
                )(func)(*args, **kwargs)

                if health_tracker:
                    health_tracker.update_health(service_name, success=True)
                return result

            except RetryExhausted:
                raise

        return wrapper

    return decorator
