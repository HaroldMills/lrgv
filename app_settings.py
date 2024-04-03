from pathlib import Path
import logging

from vesper.util.bunch import Bunch


# _root_dir_path = Path('/Users/harold/Desktop/NFC/LRGV/Synced Folders 2024')
_root_dir_path = \
    Path('/Users/harold/Desktop/NFC/LRGV/2024/Archiver Test Clip Folders')

_log_file_path = _root_dir_path / 'archive_clips.log'

_logging_level = logging.INFO

_station_names = (
    'Alamo',
    'Rio Hondo',
)

_old_bird_detector_name = 'Dick'

_old_bird_clip_file_name_re = (
    r'^'
    r'Dick_'
    r'(?P<year>\d\d\d\d)-(?P<month>\d\d)-(?P<day>\d\d)'
    r'_'
    r'(?P<hour>\d\d)\.(?P<minute>\d\d)\.(?P<second>\d\d)'
    r'_'
    r'(?P<num>\d\d)'
    r'\.(?:wav|WAV)'
    r'$')

_nighthawk_detector_name = 'Nighthawk'

_clip_file_name_re = (
    r'^'
    r'(?P<station_name>.+)'
    f'_'
    r'(?P<year>\d\d\d\d)-(?P<month>\d\d)-(?P<day>\d\d)'
    r'_'
    r'(?P<hour>\d\d)\.(?P<minute>\d\d)\.(?P<second>\d\d).(?P<millis>\d\d\d)'
    r'_'
    r'Z'
    r'_'
    r'(?P<num>\d\d)'
    r'\.(?:wav|WAV)'
    r'$')


_clip_file_wait_period = 10         # seconds


_detector_names = (
    _old_bird_detector_name,
    _nighthawk_detector_name,
)


def _get_paths(station_names, detector_names):


    def get_detector_paths(clip_dir_path, detector_name):

        detector_dir_path = clip_dir_path / detector_name

        return Bunch(
            detector_dir_path=detector_dir_path,
            archived_clip_dir_path=detector_dir_path / 'Archived',
            deferred_clip_dir_path=detector_dir_path / 'Deferred',
            incoming_clip_dir_path=detector_dir_path / 'Incoming',
            outside_clip_dir_path=detector_dir_path / 'Outside')


    def get_station_paths(station_name, detector_names):

        station_dir_path = _root_dir_path / station_name
        clip_dir_path = station_dir_path / 'Clips'

        detector_paths = {
            detector_name: get_detector_paths(clip_dir_path, detector_name)
            for detector_name in detector_names
        }

        return Bunch(
            station_dir_path=station_dir_path,
            old_bird_clip_dir_path=station_dir_path,
            clip_dir_path=clip_dir_path,
            code_dir_path=station_dir_path / 'Code',
            log_dir_path=station_dir_path / 'Logs',
            detectors=detector_paths)

    station_paths = {
        station_name: get_station_paths(station_name, detector_names)
        for station_name in station_names
    }
    
    return Bunch(
        root_dir_path=_root_dir_path,
        log_file_path=_log_file_path,
        stations=station_paths)


app_settings = Bunch(
    logging_level=_logging_level,
    station_names=_station_names,
    detector_names=_detector_names,
    paths=_get_paths(_station_names, _detector_names),
    old_bird_detector_name=_old_bird_detector_name,
    old_bird_clip_file_name_re=_old_bird_clip_file_name_re,
    clip_file_name_re=_clip_file_name_re,
    clip_file_wait_period=_clip_file_wait_period)
