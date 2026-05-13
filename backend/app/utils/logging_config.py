from datetime import datetime  # noqa: F401 - needed for monkeypatching in tests
from app.utils.logging.logging_config import (  # noqa: F401
    RequestLogger,
    request_logger,
)

from app.utils.logging.logging_config import _setup_logging_impl


def setup_logging(log_level: str = "INFO", log_dir: str = "logs", app_name: str = "baixing_law") -> None:
    _setup_logging_impl(log_level=log_level, log_dir=log_dir, app_name=app_name, _datetime=datetime)
