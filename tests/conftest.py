from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager

import grpc
import pytest
from ortools.sat import cp_model_pb2

from fanscore.optimizer.v1 import optimizer_pb2_grpc
from optimizer.config import Config
from optimizer.server import create_server


@pytest.fixture
def running_server():
    @contextmanager
    def run(**options):
        config = Config(**options)
        with ThreadPoolExecutor(
            max_workers=config.max_concurrent_solves + 2
        ) as executor:
            server, _ = create_server(config, executor)
            port = server.add_insecure_port("127.0.0.1:0")
            server.start()
            address = f"127.0.0.1:{port}"
            try:
                with grpc.insecure_channel(address) as channel:
                    grpc.channel_ready_future(channel).result(timeout=5)
                    yield optimizer_pb2_grpc.OptimizerServiceStub(channel), address
            finally:
                server.stop(0).wait(timeout=5)

    return run


@pytest.fixture
def knapsack():
    model = cp_model_pb2.CpModelProto()
    for _ in range(3):
        model.variables.add(domain=[0, 1])
    model.constraints.add().linear.CopyFrom(
        cp_model_pb2.LinearConstraintProto(
            vars=[0, 1, 2], coeffs=[6, 5, 3], domain=[0, 8]
        )
    )
    model.objective.CopyFrom(
        cp_model_pb2.CpObjectiveProto(
            vars=[0, 1, 2], coeffs=[-6, -5, -3], scaling_factor=-1
        )
    )
    return model


@pytest.fixture
def hard_model():
    # A dense Max-Cut problem gives cancellation a running native search to stop.
    import random

    rng = random.Random(1)
    model = cp_model_pb2.CpModelProto()
    for _ in range(160):
        model.variables.add(domain=[0, 1])
    edges = rng.sample([(a, b) for a in range(160) for b in range(a + 1, 160)], 2500)
    for a, b in edges:
        cut = len(model.variables)
        model.variables.add(domain=[0, 1])
        model.constraints.add().bool_xor.literals.extend([a, b, -cut - 1])
        model.objective.vars.append(cut)
        model.objective.coeffs.append(-1)
    model.objective.scaling_factor = -1
    return model
