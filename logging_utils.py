import logging

from app_settings import app_settings


_LOG_MESSAGE_FORMAT = ' | '.join((
    '%(asctime)s.%(msecs)03d', '%(name)s', '%(levelname)s', '%(message)s'))
_LOG_MESSAGE_DATE_FORMAT = '%Y-%m-%d %H:%M:%S'


def configure_logging():
    s = app_settings
    logging.basicConfig(
        level=s.logging_level, filename=s.paths.log_file_path,
        format=_LOG_MESSAGE_FORMAT, datefmt=_LOG_MESSAGE_DATE_FORMAT)
