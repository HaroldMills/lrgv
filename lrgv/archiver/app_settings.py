from pathlib import Path
import logging

from environs import Env

from lrgv.util.bunch import Bunch


# _STATION_DATA_DIR_PATH = \
#     Path('/Users/harold/Desktop/NFC/LRGV/Synced Folders 2024')
_STATION_DATA_DIR_PATH = \
    Path('/Users/harold/Desktop/NFC/LRGV/2024/Archiver Test Clip Folders')

# The archiver only uses the following when archiving to a local achive
# (specifically, in the `ClipAudioFileCopier` class). It does not use it
# when archiving to a cloud archive.
_ARCHIVE_DIR_PATH = Path('/Users/harold/Desktop/NFC/LRGV/2024/Test Archive')

_LOG_FILE_PATH = None
# _LOG_FILE_PATH = _STATION_DATA_DIR_PATH / 'archive_clips.log'

_LOGGING_LEVEL = logging.INFO

_STATION_NAMES = (
    'Alamo',
    'Rio Hondo',
)

_DETECTOR_NAMES = ('Dick', 'Nighthawk')

_CLIP_FILE_WAIT_PERIOD = 10         # seconds

_SECRET_FILE_PATH = Path(__file__).parent / 'secrets/secrets.env'


env = Env()
env.read_env(_SECRET_FILE_PATH)


def _get_paths(station_names, detector_names):


    def get_detector_paths(clip_dir_path, detector_name):

        detector_dir_path = clip_dir_path / detector_name

        return Bunch(
            detector_dir_path=detector_dir_path,
            archived_clip_dir_path=detector_dir_path / 'Archived',
            created_clip_dir_path=detector_dir_path / 'Created',
            incoming_clip_dir_path=detector_dir_path / 'Incoming')


    def get_station_paths(station_name, detector_names):

        station_dir_path = _STATION_DATA_DIR_PATH / station_name
        clip_dir_path = station_dir_path / 'Clips'

        detector_paths = {
            detector_name: get_detector_paths(clip_dir_path, detector_name)
            for detector_name in detector_names
        }

        return Bunch(
            station_dir_path=station_dir_path,
            clip_dir_path=clip_dir_path,
            code_dir_path=station_dir_path / 'Code',
            log_dir_path=station_dir_path / 'Logs',
            detectors=detector_paths)

    station_paths = {
        station_name: get_station_paths(station_name, detector_names)
        for station_name in station_names
    }
    
    return Bunch(
        station_data_dir_path=_STATION_DATA_DIR_PATH,
        archive_dir_path=_ARCHIVE_DIR_PATH,
        log_file_path=_LOG_FILE_PATH,
        stations=station_paths)


def _get_vesper_settings():
    return Bunch(
        archive_url=env('LRGV_VESPER_ARCHIVE_URL'),
        username=env('LRGV_VESPER_USERNAME'),
        password=env('LRGV_VESPER_PASSWORD'))


def _get_aws_settings():
    return Bunch(
        access_key_id=env('LRGV_AWS_ACCESS_KEY_ID'),
        secret_access_key=env('LRGV_AWS_SECRET_ACCESS_KEY'),
        region_name=env('LRGV_AWS_REGION_NAME'),
        s3_clip_bucket_name='old-bird-lrgv-2024',
        s3_clip_folder_path='Clips/')


app_settings = Bunch(
    logging_level=_LOGGING_LEVEL,
    station_names=_STATION_NAMES,
    detector_names=_DETECTOR_NAMES,
    paths=_get_paths(_STATION_NAMES, _DETECTOR_NAMES),
    clip_file_wait_period=_CLIP_FILE_WAIT_PERIOD,
    vesper=_get_vesper_settings(),
    aws=_get_aws_settings())
