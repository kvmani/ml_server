import logging
import signal
import sys


def install_signal_handlers():
    """Install SIGTERM and SIGINT handlers for graceful shutdown."""

    def _handle(signum, frame):  # pragma: no cover - signal paths hard to test
        logging.getLogger(__name__).info("Received signal %s - shutting down", signum)
        sys.exit(0)

    for sig in (signal.SIGTERM, signal.SIGINT):
        signal.signal(sig, _handle)
