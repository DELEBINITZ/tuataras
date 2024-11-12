import time
import logging

logger = logging.getLogger(__name__)


def retry_on_failure(func, MAX_RETRIES: int = 3, RETRY_DELAY: int = 5):
    def wrapper(*args, **kwargs):
        attempts = 0
        while attempts < MAX_RETRIES:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                attempts += 1
                logger.warning(
                    f"Retry {attempts}/{MAX_RETRIES} for function {func.__name__} after error: {e}"
                )
                if attempts >= MAX_RETRIES:
                    raise
                time.sleep(RETRY_DELAY)

    return wrapper
