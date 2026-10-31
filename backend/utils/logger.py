import logging
import sys

_CONFIGURED = False


def get_logger(name: str) -> logging.Logger:
    global _CONFIGURED
    if not _CONFIGURED:
        logging.basicConfig(
            level=logging.INFO,
            stream=sys.stdout,
            format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
        )
        _CONFIGURED = True
    return logging.getLogger(name)
