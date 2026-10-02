import math
import os
from dataclasses import dataclass


def health_address_from_env() -> str:
    return os.getenv("OPTIMIZER_HEALTH_ADDRESS", "127.0.0.1:50051")


@dataclass(frozen=True)
class Config:
    listen_address: str = "[::]:50051"
    max_solve_seconds: float = 3.0
    max_workers: int = 1
    max_concurrent_solves: int = 2
    max_message_bytes: int = 8 * 1024 * 1024
    shutdown_grace_seconds: float = 5.0

    def __post_init__(self) -> None:
        if not self.listen_address:
            raise ValueError("listen_address must not be empty")
        for name in ("max_solve_seconds", "shutdown_grace_seconds"):
            value = getattr(self, name)
            if not math.isfinite(value) or value <= 0:
                raise ValueError(f"{name} must be finite and greater than zero")
        for name in ("max_workers", "max_concurrent_solves", "max_message_bytes"):
            if getattr(self, name) <= 0:
                raise ValueError(f"{name} must be greater than zero")

    @classmethod
    def from_env(cls) -> Config:
        defaults = cls()
        return cls(
            listen_address=os.getenv(
                "OPTIMIZER_LISTEN_ADDRESS", defaults.listen_address
            ),
            max_solve_seconds=float(
                os.getenv(
                    "OPTIMIZER_MAX_SOLVE_SECONDS", str(defaults.max_solve_seconds)
                )
            ),
            max_workers=int(
                os.getenv("OPTIMIZER_MAX_WORKERS", str(defaults.max_workers))
            ),
            max_concurrent_solves=int(
                os.getenv(
                    "OPTIMIZER_MAX_CONCURRENT_SOLVES",
                    str(defaults.max_concurrent_solves),
                )
            ),
            max_message_bytes=int(
                os.getenv(
                    "OPTIMIZER_MAX_MESSAGE_BYTES", str(defaults.max_message_bytes)
                )
            ),
            shutdown_grace_seconds=float(
                os.getenv(
                    "OPTIMIZER_SHUTDOWN_GRACE_SECONDS",
                    str(defaults.shutdown_grace_seconds),
                )
            ),
        )
