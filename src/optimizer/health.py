import argparse

import grpc
from grpc_health.v1 import health_pb2, health_pb2_grpc

from optimizer.config import health_address_from_env
from optimizer.v1 import SERVICE_NAME


def check_health(address: str) -> bool:
    with grpc.insecure_channel(address) as channel:
        response = health_pb2_grpc.HealthStub(channel).Check(
            health_pb2.HealthCheckRequest(service=SERVICE_NAME),
            timeout=2,
        )
        return response.status == health_pb2.HealthCheckResponse.SERVING


def main() -> None:
    parser = argparse.ArgumentParser(description="Check optimizer gRPC health")
    parser.add_argument("--address", default=health_address_from_env())
    args = parser.parse_args()
    try:
        healthy = check_health(args.address)
    except grpc.RpcError:
        healthy = False
    raise SystemExit(0 if healthy else 1)


if __name__ == "__main__":
    main()
