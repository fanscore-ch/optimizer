"""Run Go client tests against a temporary Python gRPC server."""

import os
import pathlib
import subprocess
from concurrent.futures import ThreadPoolExecutor

from optimizer.config import Config
from optimizer.server import create_server

ROOT = pathlib.Path(__file__).resolve().parents[1]


def main() -> None:
    config = Config()
    with ThreadPoolExecutor(max_workers=config.max_concurrent_solves + 2) as executor:
        server, _ = create_server(config, executor)
        port = server.add_insecure_port("127.0.0.1:0")
        if port == 0:
            raise RuntimeError("could not bind integration test server")
        server.start()
        try:
            subprocess.run(
                ["go", "test", "-count=1", "./..."],
                cwd=ROOT / "gen/go",
                env=os.environ | {"OPTIMIZER_TEST_ADDRESS": f"127.0.0.1:{port}"},
                check=True,
            )
        finally:
            server.stop(0).wait()


if __name__ == "__main__":
    main()
