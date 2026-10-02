from concurrent.futures import ThreadPoolExecutor

import grpc
from grpc_health.v1 import health, health_pb2, health_pb2_grpc

from optimizer.config import Config
from optimizer.handler import OptimizerServicer
from optimizer.v1 import SERVICE_NAME, optimizer_pb2_grpc


def create_server(
    config: Config, executor: ThreadPoolExecutor
) -> tuple[grpc.Server, health.HealthServicer]:
    server = grpc.server(
        executor,
        maximum_concurrent_rpcs=config.max_concurrent_solves + 2,
        options=(
            ("grpc.max_receive_message_length", config.max_message_bytes),
            ("grpc.max_send_message_length", config.max_message_bytes),
        ),
    )
    optimizer_pb2_grpc.add_OptimizerServiceServicer_to_server(
        OptimizerServicer(config), server
    )
    health_service = health.HealthServicer()
    health_pb2_grpc.add_HealthServicer_to_server(health_service, server)
    health_service.set("", health_pb2.HealthCheckResponse.SERVING)
    health_service.set(SERVICE_NAME, health_pb2.HealthCheckResponse.SERVING)
    return server, health_service
