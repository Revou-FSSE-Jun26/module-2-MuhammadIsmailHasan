import logging
import os
from logging.handlers import TimedRotatingFileHandler

LOG_FORMAT = '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
DATE_FORMAT = '%Y-%m-%d %H:%M:%S'


def configure_logging(flask_app):
    level = getattr(logging, flask_app.config.get('LOG_LEVEL', 'INFO').upper(), logging.INFO)
    formatter = logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT)

    logger = flask_app.logger
    logger.setLevel(level)

    for existing in list(logger.handlers):
        logger.removeHandler(existing)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(level)
    logger.addHandler(console_handler)

    if flask_app.config.get('LOG_TO_FILE', True):
        log_dir = flask_app.config.get('LOG_DIR', 'logs')
        os.makedirs(log_dir, exist_ok=True)
        log_path = os.path.join(log_dir, flask_app.config.get('LOG_FILE', 'app.log'))

        file_handler = TimedRotatingFileHandler(
            log_path,
            when='midnight',
            interval=1,
            backupCount=flask_app.config.get('LOG_BACKUP_COUNT', 30),
        )
        file_handler.suffix = '%Y-%m-%d'
        file_handler.setFormatter(formatter)
        file_handler.setLevel(level)
        logger.addHandler(file_handler)

    logger.propagate = False
    return logger
