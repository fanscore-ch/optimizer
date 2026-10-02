import logging
import signal
from concurrent.futures import ThreadPoolExecutor

from optimizer.config import Config
from optimizer.server import create_server

logger = logging.getLogger(__name__)


def main() -> None:
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s"
    )
    config = Config.from_env()
    with ThreadPoolExecutor(max_workers=config.max_concurrent_solves + 2) as executor:
        server, health_service = create_server(config, executor)
        if server.add_insecure_port(config.listen_address) == 0:
            raise RuntimeError(f"could not bind {config.listen_address}")

        def shutdown(signum: int, _frame: object) -> None:
            logger.info("shutdown signal=%d", signum)
            health_service.enter_graceful_shutdown()
            server.stop(config.shutdown_grace_seconds)

        signal.signal(signal.SIGTERM, shutdown)
        signal.signal(signal.SIGINT, shutdown)
        server.start()
        logger.info("optimizer listening on %s", config.listen_address)
        server.wait_for_termination()


if __name__ == "__main__":
    main()
