import threading
import time

import grpc
import pytest
from google.rpc import error_details_pb2
from grpc_status import rpc_status
from ortools.sat import cp_model_pb2, sat_parameters_pb2

from fanscore.optimizer.v1 import optimizer_pb2
from optimizer import grpc_service
from optimizer.health import check_health
from optimizer.solver import Solver


def assert_error_details(error, reason, *, metadata=None, fields=()):
    status = rpc_status.from_call(error)
    assert status is not None
    types = [detail.type_url for detail in status.details]
    assert len(types) == len(set(types)), "error detail types must be unique"
    info = error_details_pb2.ErrorInfo()
    assert any(detail.Unpack(info) for detail in status.details)
    assert info.domain == "optimizer.fanscore.ch"
    assert info.reason == reason
    if metadata is not None:
        assert dict(info.metadata) == metadata
    bad_request = error_details_pb2.BadRequest()
    violations = []
    for detail in status.details:
        if detail.Unpack(bad_request):
            violations = list(bad_request.field_violations)
    assert [violation.field for violation in violations] == list(fields)
    assert all(violation.description for violation in violations)
    return info


def test_solves_knapsack_over_grpc(running_server, knapsack):
    with running_server() as (stub, address):
        response = stub.Solve(optimizer_pb2.SolveRequest(model=knapsack), timeout=2)
        assert response.result.status == cp_model_pb2.OPTIMAL
        assert list(response.result.solution) == [0, 1, 1]
        assert response.result.objective_value == 8
        assert check_health(address)


def test_returns_infeasible_as_solver_result(running_server):
    model = cp_model_pb2.CpModelProto()
    model.variables.add(domain=[0, 1])
    model.constraints.add().linear.CopyFrom(
        cp_model_pb2.LinearConstraintProto(vars=[0], coeffs=[1], domain=[2, 2])
    )
    with running_server() as (stub, _):
        result = stub.Solve(optimizer_pb2.SolveRequest(model=model), timeout=2).result
    assert result.status == cp_model_pb2.INFEASIBLE
    assert not result.solution


def test_rejects_invalid_model_with_field_violation(running_server):
    model = cp_model_pb2.CpModelProto()
    model.variables.add(domain=[0, 1])
    model.constraints.add().linear.CopyFrom(
        cp_model_pb2.LinearConstraintProto(vars=[99], coeffs=[1], domain=[0, 1])
    )
    with running_server() as (stub, _), pytest.raises(grpc.RpcError) as error:
        stub.Solve(optimizer_pb2.SolveRequest(model=model), timeout=2)
    assert error.value.code() == grpc.StatusCode.INVALID_ARGUMENT
    assert_error_details(error.value, "MODEL_INVALID", fields=("model",))


def test_empty_present_model_is_valid(running_server):
    with running_server() as (stub, _):
        result = stub.Solve(
            optimizer_pb2.SolveRequest(model=cp_model_pb2.CpModelProto()), timeout=2
        ).result
    assert result.status == cp_model_pb2.OPTIMAL


def test_native_parameter_error_does_not_blame_model(running_server, knapsack):
    with running_server(max_concurrent_solves=1, max_workers=10001) as (stub, _):
        with pytest.raises(grpc.RpcError) as error:
            stub.Solve(
                optimizer_pb2.SolveRequest(
                    model=knapsack,
                    parameters=sat_parameters_pb2.SatParameters(num_workers=10001),
                ),
                timeout=2,
            )
        assert error.value.code() == grpc.StatusCode.INVALID_ARGUMENT
        info = assert_error_details(error.value, "INVALID_INPUT")
        assert "num_workers" in info.metadata["validationError"]


def test_requires_model(running_server):
    with running_server() as (stub, _), pytest.raises(grpc.RpcError) as error:
        stub.Solve(optimizer_pb2.SolveRequest(), timeout=2)
    assert error.value.code() == grpc.StatusCode.INVALID_ARGUMENT
    assert error.value.details() == "model: value is required"
    assert_error_details(error.value, "MODEL_REQUIRED", fields=("model",))


@pytest.mark.parametrize(
    "parameters",
    [
        sat_parameters_pb2.SatParameters(max_time_in_seconds=-1),
        sat_parameters_pb2.SatParameters(max_time_in_seconds=float("nan")),
        sat_parameters_pb2.SatParameters(num_workers=-1),
        sat_parameters_pb2.SatParameters(num_search_workers=1),
        sat_parameters_pb2.SatParameters(random_seed=-1),
        sat_parameters_pb2.SatParameters(relative_gap_limit=float("inf")),
        sat_parameters_pb2.SatParameters(debug_crash_if_presolve_breaks_hint=True),
        sat_parameters_pb2.SatParameters(
            num_search_workers=1, log_search_progress=True
        ),
    ],
)
def test_rejects_invalid_or_unsupported_parameters(
    running_server, knapsack, parameters
):
    with running_server(max_concurrent_solves=1) as (stub, _):
        with pytest.raises(grpc.RpcError) as error:
            stub.Solve(
                optimizer_pb2.SolveRequest(model=knapsack, parameters=parameters),
                timeout=5,
            )
        assert error.value.code() == grpc.StatusCode.INVALID_ARGUMENT
        names = sorted(field.name for field, _ in parameters.ListFields())
        if names[0] in (
            "num_search_workers",
            "debug_crash_if_presolve_breaks_hint",
            "log_search_progress",
        ):
            assert (
                error.value.details() == f"unsupported parameters: {', '.join(names)}"
            )
            assert_error_details(
                error.value,
                "UNSUPPORTED_PARAMETERS",
                metadata={"parameters": ", ".join(names)},
                fields=tuple(f"parameters.{name}" for name in names),
            )
        else:
            info = assert_error_details(
                error.value,
                "INVALID_PARAMETER",
                fields=(f"parameters.{names[0]}",),
            )
            assert info.metadata["parameter"] == names[0]
            assert info.metadata["value"] == str(parameters.ListFields()[0][1])
            assert (
                error.value.details()
                == f"{names[0]} must be {info.metadata['requirement']}"
            )
        result = stub.Solve(
            optimizer_pb2.SolveRequest(model=knapsack), timeout=5
        ).result
        assert result.status == cp_model_pb2.OPTIMAL


def test_capacity_rejection_keeps_health_available(
    running_server, knapsack, monkeypatch
):
    entered = threading.Event()
    release = threading.Event()

    class PausedSolver(Solver):
        def solve(self, remaining_seconds):
            entered.set()
            assert release.wait(3)
            return super().solve(remaining_seconds)

    monkeypatch.setattr(grpc_service, "Solver", PausedSolver)
    with running_server(max_concurrent_solves=1) as (stub, address):
        first = stub.Solve.future(optimizer_pb2.SolveRequest(model=knapsack), timeout=5)
        try:
            assert entered.wait(2)
            with pytest.raises(grpc.RpcError) as error:
                stub.Solve(optimizer_pb2.SolveRequest(model=knapsack), timeout=2)
            assert error.value.code() == grpc.StatusCode.RESOURCE_EXHAUSTED
            assert error.value.details() == "solver capacity exhausted"
            assert_error_details(
                error.value,
                "SOLVER_CAPACITY_EXHAUSTED",
                metadata={"maxConcurrentSolves": "1"},
            )
            assert check_health(address)
        finally:
            release.set()
        assert first.result(timeout=3).result.status == cp_model_pb2.OPTIMAL


@pytest.mark.parametrize("termination", ["cancel", "deadline"])
def test_rpc_termination_stops_native_search(
    running_server, hard_model, knapsack, monkeypatch, termination
):
    entered = threading.Event()
    cancelled = threading.Event()
    completed = threading.Event()

    class ObservedSolver(Solver):
        def solve(self, remaining_seconds):
            entered.set()
            try:
                # Isolate deadline cancellation from CP-SAT's own time limit.
                limit = 20 if termination == "deadline" else remaining_seconds
                return super().solve(limit)
            finally:
                completed.set()

        def cancel(self):
            cancelled.set()
            super().cancel()

    monkeypatch.setattr(grpc_service, "Solver", ObservedSolver)
    with running_server(max_concurrent_solves=1, max_solve_seconds=20) as (stub, _):
        timeout = 1 if termination == "deadline" else 10
        future = stub.Solve.future(
            optimizer_pb2.SolveRequest(model=hard_model), timeout=timeout
        )
        assert entered.wait(5)
        if termination == "cancel":
            assert future.cancel()
            with pytest.raises(grpc.FutureCancelledError):
                future.result()
        else:
            with pytest.raises(grpc.RpcError) as error:
                future.result(timeout=5)
            assert error.value.code() == grpc.StatusCode.DEADLINE_EXCEEDED
        assert cancelled.wait(5)
        assert completed.wait(5), "native search continued after RPC termination"
        # The native search must actually release capacity, not just end the RPC.
        expires = time.monotonic() + 3
        while True:
            try:
                result = stub.Solve(
                    optimizer_pb2.SolveRequest(model=knapsack), timeout=1
                ).result
                break
            except grpc.RpcError as error:
                if (
                    error.code() != grpc.StatusCode.RESOURCE_EXHAUSTED
                    or time.monotonic() >= expires
                ):
                    raise
                time.sleep(0.05)
        assert result.status == cp_model_pb2.OPTIMAL


def test_server_time_limit_bounds_native_search(
    running_server, hard_model, monkeypatch
):
    limits = []

    class ObservedSolver(Solver):
        def solve(self, remaining_seconds):
            limits.append(remaining_seconds)
            return super().solve(remaining_seconds)

    monkeypatch.setattr(grpc_service, "Solver", ObservedSolver)
    with running_server(max_solve_seconds=0.2) as (stub, _):
        result = stub.Solve(
            optimizer_pb2.SolveRequest(model=hard_model), timeout=3
        ).result
    assert len(limits) == 1
    assert 0 < limits[0] <= 0.2
    assert result.status in (
        cp_model_pb2.UNKNOWN,
        cp_model_pb2.FEASIBLE,
        cp_model_pb2.OPTIMAL,
    )
    assert result.wall_time < 0.7


def test_message_size_is_bounded(running_server):
    model = cp_model_pb2.CpModelProto(name="x" * 2048)
    with (
        running_server(max_message_bytes=1024) as (stub, _),
        pytest.raises(grpc.RpcError) as error,
    ):
        stub.Solve(optimizer_pb2.SolveRequest(model=model), timeout=2)
    assert error.value.code() == grpc.StatusCode.RESOURCE_EXHAUSTED
    # gRPC core rejects the payload before the application handler is invoked.
    assert rpc_status.from_call(error.value) is None


def test_unexpected_failure_is_structured_and_releases_capacity(
    running_server, knapsack, monkeypatch, caplog
):
    def fail(*args, **kwargs):
        raise RuntimeError("private diagnostic")

    with running_server(max_concurrent_solves=1) as (stub, _):
        with monkeypatch.context() as patch:
            patch.setattr(Solver, "solve", fail)
            with pytest.raises(grpc.RpcError) as error:
                stub.Solve(optimizer_pb2.SolveRequest(model=knapsack), timeout=2)
        assert error.value.code() == grpc.StatusCode.INTERNAL
        assert_error_details(error.value, "INTERNAL_ERROR")
        assert (
            b"private diagnostic"
            not in rpc_status.from_call(error.value).SerializeToString()
        )
        assert "private diagnostic" in caplog.text
        assert (
            stub.Solve(
                optimizer_pb2.SolveRequest(model=knapsack), timeout=2
            ).result.status
            == cp_model_pb2.OPTIMAL
        )
