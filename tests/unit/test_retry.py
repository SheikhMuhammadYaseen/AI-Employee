"""Unit tests for retry decorator with exponential backoff (T010)."""

import time
import unittest
from unittest.mock import MagicMock, patch

from src.recovery.retry import retry, retry_with_health, RetryExhausted


class TestRetryDecorator(unittest.TestCase):
    """Test the @retry decorator."""

    def test_success_on_first_attempt(self):
        """Function succeeds on first call — no retries."""
        call_count = 0

        @retry(max_attempts=3)
        def succeed():
            nonlocal call_count
            call_count += 1
            return "ok"

        result = succeed()
        assert result == "ok"
        assert call_count == 1

    def test_success_on_second_attempt(self):
        """Function fails once then succeeds — one retry."""
        call_count = 0

        @retry(max_attempts=3, backoff_base=0.01, backoff_factor=1)
        def flaky():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ConnectionError("fail")
            return "ok"

        result = flaky()
        assert result == "ok"
        assert call_count == 2

    def test_all_attempts_exhausted(self):
        """Function fails all attempts — raises RetryExhausted."""

        @retry(max_attempts=3, backoff_base=0.01, backoff_factor=1)
        def always_fail():
            raise ConnectionError("always fails")

        with self.assertRaises(RetryExhausted) as ctx:
            always_fail()

        assert ctx.exception.attempts == 3
        assert isinstance(ctx.exception.original_exception, ConnectionError)

    def test_non_retryable_exception_not_retried(self):
        """Non-retryable exceptions propagate immediately."""
        call_count = 0

        @retry(max_attempts=3, retryable_exceptions=(ConnectionError,))
        def type_error():
            nonlocal call_count
            call_count += 1
            raise ValueError("not retryable")

        with self.assertRaises(ValueError):
            type_error()

        assert call_count == 1

    def test_backoff_timing(self):
        """Verify exponential backoff delays are correct."""
        delays = []

        def on_retry_cb(attempt, exc, delay):
            delays.append(delay)

        @retry(max_attempts=4, backoff_base=1, backoff_factor=2, on_retry=on_retry_cb)
        def always_fail():
            raise ConnectionError("fail")

        with patch("src.recovery.retry.time.sleep") as mock_sleep:
            try:
                always_fail()
            except RetryExhausted:
                pass

        # Delays: 1*2^0=1, 1*2^1=2, 1*2^2=4
        assert mock_sleep.call_count == 3
        sleep_args = [call.args[0] for call in mock_sleep.call_args_list]
        assert sleep_args == [1, 2, 4]

    def test_on_failure_callback(self):
        """on_failure callback is called when all retries exhausted."""
        failure_cb = MagicMock()

        @retry(max_attempts=2, backoff_base=0.01, on_failure=failure_cb)
        def fail():
            raise ConnectionError("done")

        try:
            fail()
        except RetryExhausted:
            pass

        failure_cb.assert_called_once()
        args = failure_cb.call_args[0]
        assert isinstance(args[0], ConnectionError)
        assert args[1] == 2

    def test_timeout_error_retried(self):
        """TimeoutError is retryable by default."""
        call_count = 0

        @retry(max_attempts=2, backoff_base=0.01)
        def timeout():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise TimeoutError("timeout")
            return "ok"

        assert timeout() == "ok"
        assert call_count == 2

    def test_os_error_retried(self):
        """OSError is retryable by default."""
        call_count = 0

        @retry(max_attempts=2, backoff_base=0.01)
        def os_err():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise OSError("os error")
            return "ok"

        assert os_err() == "ok"

    def test_custom_retryable_exceptions(self):
        """Custom retryable exception types are honored."""

        class CustomError(Exception):
            pass

        call_count = 0

        @retry(max_attempts=2, backoff_base=0.01, retryable_exceptions=(CustomError,))
        def custom():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise CustomError("custom")
            return "ok"

        assert custom() == "ok"

    def test_max_attempts_one(self):
        """With max_attempts=1, no retries occur."""

        @retry(max_attempts=1)
        def fail():
            raise ConnectionError("fail")

        with self.assertRaises(RetryExhausted) as ctx:
            fail()

        assert ctx.exception.attempts == 1


class TestRetryWithHealth(unittest.TestCase):
    """Test retry_with_health that integrates service health tracking."""

    def test_success_updates_health(self):
        """Successful call updates service health to operational."""
        mock_tracker = MagicMock()

        @retry_with_health("test_service", health_tracker=mock_tracker, max_attempts=1)
        def succeed():
            return "ok"

        result = succeed()
        assert result == "ok"
        mock_tracker.update_health.assert_called_with("test_service", success=True)

    def test_failure_updates_health(self):
        """Failed call updates service health with error."""
        mock_tracker = MagicMock()

        @retry_with_health(
            "test_service",
            health_tracker=mock_tracker,
            max_attempts=1,
            backoff_base=0.01,
        )
        def fail():
            raise ConnectionError("down")

        with self.assertRaises(RetryExhausted):
            fail()

        mock_tracker.update_health.assert_called_with(
            "test_service", success=False, error="down"
        )


if __name__ == "__main__":
    unittest.main()
