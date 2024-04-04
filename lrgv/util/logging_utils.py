import logging


_LOG_MESSAGE_FORMAT = ' | '.join((
    '%(asctime)s.%(msecs)03d', '%(name)s', '%(levelname)s', '%(message)s'))
_LOG_MESSAGE_DATE_FORMAT = '%Y-%m-%d %H:%M:%S'


def configure_logging(logging_level=logging.INFO, log_file_path=None):

    kwargs = dict(
        level=logging_level,
        format=_LOG_MESSAGE_FORMAT,
        datefmt=_LOG_MESSAGE_DATE_FORMAT)
    
    if log_file_path is not None:
        kwargs['filename'] = log_file_path

    logging.basicConfig(**kwargs)
