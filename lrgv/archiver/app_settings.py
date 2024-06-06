from pathlib import Path
import logging

from environs import Env

from lrgv.util.bunch import Bunch


# App mode, either 'Test' or 'Production'.
_MODE = 'Test'
# _MODE = 'Production'


if _MODE == 'Test':

    _ARCHIVE_DIR_PATH = \
        Path('/Users/harold/Desktop/NFC/LRGV/2024/Test Archive')
    
    _ACTIVE_DATA_DIR_PATH = Path(
        '/Users/harold/Desktop/NFC/LRGV/2024/Archiver Test Data/Active')
    
    _RETIRED_DATA_DIR_PATH = Path(
        '/Users/harold/Desktop/NFC/LRGV/2024/Archiver Test Data/Retired')
    
    _STATION_NAMES = ('Alamo', 'Rio Hondo')

elif _MODE == 'Production':

    _ARCHIVE_DIR_PATH = None

    _ACTIVE_DATA_DIR_PATH = \
        Path('/Users/harold/Desktop/NFC/LRGV/2024/Station Data/Active')
    
    _RETIRED_DATA_DIR_PATH = \
        Path('/Users/harold/Desktop/NFC/LRGV/2024/Station Data/Retired')
    
    # _STATION_NAMES = ('Alamo',)
    _STATION_NAMES = (
        'Alamo',
        'Donna',
        'Harlingen',
        'Port Isabel',
        'Rio Hondo',
        'Roma HS',
        'Roma RBMS'
    )
    
_ARCHIVE_REMOTE = _ARCHIVE_DIR_PATH is None

_LOG_FILE_PATH = None
# _LOG_FILE_PATH = _STATION_DATA_DIR_PATH / 'archive_clips.log'

_LOGGING_LEVEL = logging.INFO

_DETECTOR_NAMES = ('Dick', 'Nighthawk')

_CLIP_FILE_WAIT_PERIOD = 10                   # seconds
# _CLIP_FILE_RETIREMENT_WAIT_PERIOD = 10        # seconds
_CLIP_FILE_RETIREMENT_WAIT_PERIOD = 172800    # seconds

_SECRET_FILE_PATH = Path(__file__).parent / 'secrets/secrets.env'


env = Env()
env.read_env(_SECRET_FILE_PATH)


def _get_paths(station_names, detector_names):


    def get_detector_paths(
            active_clip_dir_path, retired_clip_dir_path, detector_name):

        active_dir_path = active_clip_dir_path / detector_name
        retired_dir_path = retired_clip_dir_path / detector_name

        return Bunch(
            incoming_clip_dir_path=active_dir_path / 'Incoming',
            created_clip_dir_path=active_dir_path / 'Created',
            archived_clip_dir_path=active_dir_path / 'Archived',
            retired_clip_dir_path=retired_dir_path / 'Archived')


    def get_station_paths(station_name, detector_names):

        station_dir_path = _ACTIVE_DATA_DIR_PATH / station_name
        active_clip_dir_path = station_dir_path / 'Clips'

        retired_clip_dir_path = \
            _RETIRED_DATA_DIR_PATH / station_name / 'Clips'

        detector_paths = {
            detector_name: get_detector_paths(
                active_clip_dir_path, retired_clip_dir_path, detector_name)
            for detector_name in detector_names
        }

        return Bunch(
            station_dir_path=station_dir_path,
            detectors=detector_paths)

    station_paths = {
        station_name: get_station_paths(station_name, detector_names)
        for station_name in station_names
    }
    
    return Bunch(
        archive_dir_path=_ARCHIVE_DIR_PATH,
        log_file_path=_LOG_FILE_PATH,
        stations=station_paths)


def _get_vesper_settings():
    if _ARCHIVE_REMOTE:
        return Bunch(
            archive_url=env('LRGV_REMOTE_ARCHIVE_URL'),
            username=env('LRGV_REMOTE_ARCHIVE_USERNAME'),
            password=env('LRGV_REMOTE_ARCHIVE_PASSWORD'))
    else:
        return Bunch(
            archive_url=env('LRGV_LOCAL_ARCHIVE_URL'),
            username=env('LRGV_LOCAL_ARCHIVE_USERNAME'),
            password=env('LRGV_LOCAL_ARCHIVE_PASSWORD'))


def _get_aws_settings():
    return Bunch(
        access_key_id=env('LRGV_AWS_ACCESS_KEY_ID'),
        secret_access_key=env('LRGV_AWS_SECRET_ACCESS_KEY'),
        region_name=env('LRGV_AWS_REGION_NAME'),
        s3_clip_bucket_name=env('LRGV_AWS_S3_CLIP_BUCKET_NAME'),
        s3_clip_folder_path=env('LRGV_AWS_S3_CLIP_FOLDER_PATH'))


app_settings = Bunch(
    archive_remote=_ARCHIVE_REMOTE,
    logging_level=_LOGGING_LEVEL,
    station_names=_STATION_NAMES,
    detector_names=_DETECTOR_NAMES,
    paths=_get_paths(_STATION_NAMES, _DETECTOR_NAMES),
    clip_file_wait_period=_CLIP_FILE_WAIT_PERIOD,
    clip_file_retirement_wait_period=_CLIP_FILE_RETIREMENT_WAIT_PERIOD,
    vesper=_get_vesper_settings())

if _ARCHIVE_REMOTE:
    app_settings.aws=_get_aws_settings()
