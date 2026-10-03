import pytest

from optimizer.config import Config


@pytest.mark.parametrize(
    "options",
    [
        {"max_solve_seconds": float("inf")},
        {"max_solve_seconds": 0},
        {"max_workers": 0},
        {"max_concurrent_solves": 0},
        {"max_message_bytes": -1},
        {"shutdown_grace_seconds": -1},
    ],
)
def test_invalid_configuration_is_rejected(options):
    with pytest.raises(ValueError):
        Config(**options)
