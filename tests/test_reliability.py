from app.reliability import run_with_retries


def test_retry_succeeds_after_transient_failures():
    attempts = 0
    def flaky():
        nonlocal attempts
        attempts += 1
        if attempts < 3:
            raise RuntimeError("temporary")
        return "ok"
    assert run_with_retries(flaky, max_attempts=3, backoff_seconds=0) == "ok"
    assert attempts == 3

def test_retry_raises_after_limit():
    try:
        run_with_retries(lambda: 1 / 0, max_attempts=2, backoff_seconds=0)
    except ZeroDivisionError:
        pass
    else:
        raise AssertionError("retry did not raise after the attempt limit")
