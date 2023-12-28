import logging
from logging.handlers import RotatingFileHandler


def setup_logging():
    # Configure the root logger
    logger = logging.getLogger("lambda")
    logger.setLevel(logging.DEBUG)

    # Create handlers
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)

    file_handler = RotatingFileHandler(
        filename="lambda_bot.log", maxBytes=5 * 1024 * 1024, backupCount=5
    )
    file_handler.setLevel(logging.DEBUG)

    # Create formatters and set it for handlers
    formatter = logging.Formatter("%(asctime)s:%(levelname)s:%(name)s: %(message)s")
    console_handler.setFormatter(formatter)
    file_handler.setFormatter(formatter)

    # Add handlers to the logger
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
