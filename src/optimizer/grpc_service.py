import logging
import threading
import time

import grpc
from ortools.sat import cp_model_pb2

from fanscore.optimizer.v1 import optimizer_pb2, optimizer_pb2_grpc
from optimizer.config import Config
from optimizer.errors import InvalidArgument, ServiceError
from optimizer.solver import Solver, prepare_parameters

logger = logging.getLogger(__name__)


class OptimizerServicer(optimizer_pb2_grpc.OptimizerServiceServicer):
    def __init__(self, config: Config) -> None:
        self._config = config
        self._slots = threading.BoundedSemaphore(config.max_concurrent_solves)

    def Solve(
        self, request: optimizer_pb2.SolveRequest, context: grpc.ServicerContext
    ) -> optimizer_pb2.SolveResponse:
        try:
            return self._solve(request, context)
        except ServiceError as error:
            error.abort(context)
        except Exception:
            logger.exception("unexpected solve failure")
            ServiceError(
                grpc.StatusCode.INTERNAL,
                "The solver failed unexpectedly. Contact the service operator.",
                "INTERNAL_ERROR",
            ).abort(context)

    def _solve(
        self, request: optimizer_pb2.SolveRequest, context: grpc.ServicerContext
    ) -> optimizer_pb2.SolveResponse:
        started = time.monotonic()
        if not request.HasField("model"):
            message = "model: value is required"
            raise InvalidArgument(
                message,
                "MODEL_REQUIRED",
                violations={"model": message},
            )
        if not self._slots.acquire(blocking=False):
            raise ServiceError(
                grpc.StatusCode.RESOURCE_EXHAUSTED,
                "solver capacity exhausted",
                "SOLVER_CAPACITY_EXHAUSTED",
                metadata={
                    "maxConcurrentSolves": str(self._config.max_concurrent_solves)
                },
            )
        try:
            parameters = prepare_parameters(request.parameters, self._config)
            solver = Solver(request.model, parameters)

            if not context.add_callback(solver.cancel):
                raise ServiceError(
                    grpc.StatusCode.CANCELLED,
                    "request is no longer active",
                    "REQUEST_CANCELLED",
                )
            remaining = parameters.max_time_in_seconds - (time.monotonic() - started)
            deadline = context.time_remaining()
            if deadline is not None:
                remaining = min(remaining, deadline)
            if remaining <= 0:
                raise ServiceError(
                    grpc.StatusCode.DEADLINE_EXCEEDED,
                    "solve deadline elapsed",
                    "SOLVE_DEADLINE_EXCEEDED",
                )
            if not context.is_active():
                raise ServiceError(
                    grpc.StatusCode.CANCELLED,
                    "request is no longer active",
                    "REQUEST_CANCELLED",
                )

            result = solver.solve(remaining)
            logger.info(
                "solve status=%s variables=%d constraints=%d wall_seconds=%.3f",
                cp_model_pb2.CpSolverStatus.Name(result.status),
                len(request.model.variables),
                len(request.model.constraints),
                time.monotonic() - started,
            )
            return optimizer_pb2.SolveResponse(result=result)
        finally:
            self._slots.release()
