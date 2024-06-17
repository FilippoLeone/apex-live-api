# logging_config.py
import logging

def setup_logging():
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger('websocket_server')
    return logger
