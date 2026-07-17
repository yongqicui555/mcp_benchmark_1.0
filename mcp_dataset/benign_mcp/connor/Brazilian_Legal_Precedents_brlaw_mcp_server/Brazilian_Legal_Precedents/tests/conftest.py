import logging

import pytest


@pytest.fixture(autouse=True)
def setup_logging(caplog: pytest.LogCaptureFixture) -> None:
    """Allow all log records to be captured."""
    caplog.set_level(logging.DEBUG)
