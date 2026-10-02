import os
import socket
import subprocess
import sys
import time
from pathlib import Path

import grpc

from optimizer.health import check_health


def test_cli_reads_environment_and_shuts_down_cleanly(tmp_path):
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        address = f"127.0.0.1:{listener.getsockname()[1]}"

    executable = Path(sys.executable).with_name("optimizer")
    assert executable.is_file(), (
        "optimizer CLI must be installed in the test environment"
    )
    environment = {
        key: value
        for key, value in os.environ.items()
        if not key.startswith("OPTIMIZER_")
    } | {
        "OPTIMIZER_LISTEN_ADDRESS": address,
        "OPTIMIZER_SHUTDOWN_GRACE_SECONDS": "1",
    }
    log_path = tmp_path / "optimizer.log"
    with log_path.open("w") as log:
        process = subprocess.Popen(
            [str(executable)], env=environment, stdout=log, stderr=subprocess.STDOUT
        )
        try:
            expires = time.monotonic() + 10
            while True:
                assert process.poll() is None, log_path.read_text()
                try:
                    if check_health(address):
                        break
                except grpc.RpcError:
                    pass
                assert time.monotonic() < expires, log_path.read_text()
                time.sleep(0.05)

            process.terminate()
            assert process.wait(timeout=10) == 0, log_path.read_text()
        finally:
            if process.poll() is None:
                process.kill()
                process.wait(timeout=5)
