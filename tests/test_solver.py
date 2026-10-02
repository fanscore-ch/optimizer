from ortools.sat import cp_model_pb2, sat_parameters_pb2

from optimizer.solver import Solver


def test_cancellation_before_solve_stops_native_search(hard_model):
    solver = Solver(hard_model, sat_parameters_pb2.SatParameters(num_workers=1))
    solver.cancel()

    result = solver.solve(10)

    assert result.status == cp_model_pb2.UNKNOWN
    assert not result.solution
    assert result.wall_time < 2
