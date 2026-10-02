import logging
import threading
import time

import grpc
from ortools.sat import cp_model_pb2

from optimizer.config import Config
from optimizer.solver import Solver, prepare_parameters
from optimizer.v1 import optimizer_pb2, optimizer_pb2_grpc

logger = logging.getLogger(__name__)


class OptimizerServicer(optimizer_pb2_grpc.OptimizerServiceServicer):
    def __init__(self, config: Config) -> None:
        self._config = config
        self._slots = threading.BoundedSemaphore(config.max_concurrent_solves)

    def Solve(
        self, request: optimizer_pb2.SolveRequest, context: grpc.ServicerContext
    ) -> optimizer_pb2.SolveResponse:
        started = time.monotonic()
        if not request.HasField("model"):
            context.abort(grpc.StatusCode.INVALID_ARGUMENT, "model is required")
        if not self._slots.acquire(blocking=False):
            context.abort(
                grpc.StatusCode.RESOURCE_EXHAUSTED, "solver capacity exhausted"
            )
        try:
            try:
                parameters = prepare_parameters(request.parameters, self._config)
                solver = Solver(request.model, parameters)
            except ValueError as error:
                context.abort(grpc.StatusCode.INVALID_ARGUMENT, str(error))

            if not context.add_callback(solver.cancel):
                context.abort(grpc.StatusCode.CANCELLED, "request is no longer active")
            remaining = parameters.max_time_in_seconds - (time.monotonic() - started)
            deadline = context.time_remaining()
            if deadline is not None:
                remaining = min(remaining, deadline)
            if remaining <= 0:
                context.abort(
                    grpc.StatusCode.DEADLINE_EXCEEDED, "solve deadline elapsed"
                )
            if not context.is_active():
                context.abort(grpc.StatusCode.CANCELLED, "request is no longer active")

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
