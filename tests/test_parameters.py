from ortools.sat import sat_parameters_pb2

from optimizer.config import Config
from optimizer.solver import prepare_parameters


def test_defaults_use_server_limits():
    params = prepare_parameters(sat_parameters_pb2.SatParameters(), Config())
    assert params.max_time_in_seconds == 3
    assert params.num_workers == 1


def test_requested_limits_are_capped_without_mutating_request():
    requested = sat_parameters_pb2.SatParameters(max_time_in_seconds=60, num_workers=32)
    params = prepare_parameters(requested, Config(max_solve_seconds=2, max_workers=4))
    assert params.max_time_in_seconds == 2
    assert params.num_workers == 4
    assert requested.max_time_in_seconds == 60
    assert requested.num_workers == 32


def test_lower_client_limits_are_respected():
    params = prepare_parameters(
        sat_parameters_pb2.SatParameters(max_time_in_seconds=0.5, num_workers=1),
        Config(max_workers=2),
    )
    assert params.max_time_in_seconds == 0.5
    assert params.num_workers == 1
