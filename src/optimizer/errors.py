from typing import NoReturn

import grpc
from google.rpc import error_details_pb2, status_pb2
from grpc_status import rpc_status

ERROR_DOMAIN = "optimizer.fanscore.ch"


class ServiceError(Exception):
    """An application error with a stable, machine-readable identity."""

    def __init__(
        self,
        code: grpc.StatusCode,
        message: str,
        reason: str,
        *,
        metadata: dict[str, str] | None = None,
        violations: dict[str, str] | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.reason = reason
        self.metadata = metadata or {}
        self.violations = violations or {}

    def abort(self, context: grpc.ServicerContext) -> NoReturn:
        status = status_pb2.Status(code=self.code.value[0], message=str(self))
        status.details.add().Pack(
            error_details_pb2.ErrorInfo(
                reason=self.reason, domain=ERROR_DOMAIN, metadata=self.metadata
            )
        )
        if self.violations:
            bad_request = error_details_pb2.BadRequest()
            for field, description in self.violations.items():
                bad_request.field_violations.add(field=field, description=description)
            status.details.add().Pack(bad_request)
        context.abort_with_status(rpc_status.to_status(status))


class InvalidArgument(ServiceError, ValueError):
    def __init__(
        self,
        message: str,
        reason: str,
        *,
        metadata: dict[str, str] | None = None,
        violations: dict[str, str] | None = None,
    ) -> None:
        super().__init__(
            grpc.StatusCode.INVALID_ARGUMENT,
            message,
            reason,
            metadata=metadata,
            violations=violations,
        )
