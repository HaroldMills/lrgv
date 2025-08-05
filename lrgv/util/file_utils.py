from datetime import datetime as DateTime
from pathlib import Path
from zoneinfo import ZoneInfo
import logging

from lrgv.util.bunch import Bunch


logger = logging.getLogger(__name__)


UTC_TIME_ZONE = ZoneInfo('UTC')


def parse_recording_file_name(name):

    stem = Path(name).stem

    parts = stem.split('_', 1)

    if len(parts) != 2:
        logger.info(
            f'Could not parse recording audio file name "{name}". '
            f'File will be ignored.')
        return None
    
    station_name, start_time = parts

    try:
        start_time = DateTime.strptime(start_time, '%Y-%m-%d_%H.%M.%S_Z')
    except Exception:
        logger.info(
            f'Could not parse start time of recording audio file name '
            f'"{name}". File will be ignored.')
        return None
    
    # Set time zone to UTC.
    start_time = start_time.replace(tzinfo=UTC_TIME_ZONE)
    
    file = Bunch()
    file.name = name
    file.station_name = station_name
    file.start_time = start_time

    return file
