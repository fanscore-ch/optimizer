import math
import threading

from google.protobuf import text_format
from ortools.sat import cp_model_pb2, sat_parameters_pb2
from ortools.sat.python import cp_model_helper

from optimizer.config import Config

SUPPORTED_PARAMETERS = frozenset(
    {
        "max_time_in_seconds",
        "max_deterministic_time",
        "num_workers",
        "random_seed",
        "stop_after_first_solution",
        "relative_gap_limit",
        "absolute_gap_limit",
    }
)


def prepare_parameters(
    requested: sat_parameters_pb2.SatParameters, config: Config
) -> sat_parameters_pb2.SatParameters:
    fields = {field.name for field, _ in requested.ListFields()}
    unsupported = fields - SUPPORTED_PARAMETERS
    if unsupported:
        raise ValueError(f"unsupported parameters: {', '.join(sorted(unsupported))}")
    for name in ("max_time_in_seconds", "max_deterministic_time"):
        if requested.HasField(name):
            value = getattr(requested, name)
            if not math.isfinite(value) or value <= 0:
                raise ValueError(f"{name} must be finite and greater than zero")
    for name in ("relative_gap_limit", "absolute_gap_limit"):
        value = getattr(requested, name)
        if not math.isfinite(value) or value < 0:
            raise ValueError(f"{name} must be finite and nonnegative")
    for name in ("num_workers", "random_seed"):
        if getattr(requested, name) < 0:
            raise ValueError(f"{name} must be nonnegative")

    parameters = sat_parameters_pb2.SatParameters()
    parameters.CopyFrom(requested)
    parameters.max_time_in_seconds = min(
        requested.max_time_in_seconds, config.max_solve_seconds
    )
    workers = requested.num_workers or config.max_workers
    parameters.num_workers = min(workers, config.max_workers)
    return parameters


class Solver:
    def __init__(
        self,
        model: cp_model_pb2.CpModelProto,
        parameters: sat_parameters_pb2.SatParameters,
    ) -> None:
        # Convert generated protobuf messages to OR-Tools 9.15 native wrappers
        # through the exposed text-format API.
        self._model = cp_model_helper.CpModelProto()
        if not self._model.parse_text_format(text_format.MessageToString(model)):
            raise ValueError("model could not be parsed by OR-Tools")
        self._parameters = cp_model_helper.SatParameters()
        if not self._parameters.parse_text_format(
            text_format.MessageToString(parameters)
        ):
            raise ValueError("parameters could not be parsed by OR-Tools")
        # Construct the wrapper before registering cancellation. StopSearch then
        # also applies when the RPC ends immediately before Solve starts.
        self._wrapper = cp_model_helper.SolveWrapper()
        self._finished = threading.Event()

    def cancel(self) -> None:
        if not self._finished.is_set():
            self._wrapper.stop_search()

    def solve(self, remaining_seconds: float) -> cp_model_pb2.CpSolverResponse:
        self._parameters.max_time_in_seconds = remaining_seconds
        self._wrapper.set_parameters(self._parameters)
        try:
            native_result = self._wrapper.solve(self._model)
        finally:
            self._finished.set()
        result = cp_model_pb2.CpSolverResponse()
        text_format.Parse(str(native_result), result)
        return result
