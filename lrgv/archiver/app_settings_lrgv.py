from pathlib import Path
from zoneinfo import ZoneInfo
import logging

from environs import Env

from lrgv.util.bunch import Bunch


# App mode, either 'Test' or 'Production'.
# _MODE = 'Test'
_MODE = 'Production'

_PROJECT_NAME = 'LRGV'

_ROOT_DATA_DIR_PATH = Path('/Users/harold/Desktop/NFC/Data/Old Bird/LRGV/2025')

_ALL_STATION_NAMES = (
    'Alamo',
    'Donna',
    'Harlingen',
    'Port Isabel',
    'Rio Hondo',
    'Roma HS',
    'Roma RBMS'
)

if _MODE == 'Test':
    _TEST_DATA_DIR_PATH = _ROOT_DATA_DIR_PATH / 'Archiver Test Data'
    _ARCHIVE_DIR_PATH = _TEST_DATA_DIR_PATH / 'Test Archive'
    _STATION_DATA_DIR_PATH = _TEST_DATA_DIR_PATH / 'Test Station Data'
    _STATION_NAMES = ('Alamo', 'Port Isabel')

elif _MODE == 'Production':
    _ARCHIVE_DIR_PATH = None
    _STATION_DATA_DIR_PATH = _ROOT_DATA_DIR_PATH / 'Station Data'
    _STATION_NAMES = _ALL_STATION_NAMES

_ACTIVE_DATA_DIR_PATH = _STATION_DATA_DIR_PATH / 'Active'
_RETIRED_DATA_DIR_PATH = _STATION_DATA_DIR_PATH / 'Retired'

_ARCHIVE_REMOTE = _ARCHIVE_DIR_PATH is None

_STATION_TIME_ZONE = ZoneInfo('US/Central')

_LOG_FILE_PATH = None
# _LOG_FILE_PATH = _STATION_DATA_DIR_PATH / 'archive_clips.log'

_LOGGING_LEVEL = logging.INFO

# _DETECTOR_NAMES = ('Dick',)
_DETECTOR_NAMES = ('Nighthawk',)
# _DETECTOR_NAMES = ('Dick', 'Nighthawk')

_CLIP_FILE_WAIT_PERIOD = 60                  # seconds
# _CLIP_FILE_RETIREMENT_WAIT_PERIOD = 60       # seconds
# _CLIP_FILE_RETIREMENT_WAIT_PERIOD = 0        # seconds
_CLIP_FILE_RETIREMENT_WAIT_PERIOD = 86400    # seconds

_SECRET_FILE_PATH = Path(__file__).parent / 'secrets/secrets_lrgv.env'


env = Env()
env.read_env(_SECRET_FILE_PATH)


def _get_old_bird_clip_device_data():

    """
    Gets mapping from station name to (recorder name, mic output name) pair
    for Old Bird detector clips.
    """

    def get_device_data(station_num):
        recorder_name = f'Dick-r {station_num}'
        mic_output_name = f'21c {station_num} Dick-r Output'
        return (recorder_name, mic_output_name)
    
    return dict(
        (n, get_device_data(i))
        for i, n in enumerate(_ALL_STATION_NAMES))
    

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

        station_dir_name = f'{_PROJECT_NAME} - {station_name}'
        station_dir_path = _ACTIVE_DATA_DIR_PATH / station_dir_name
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
        server_url=env('REMOTE_SERVER_URL')
        archive_url_base=env('REMOTE_ARCHIVE_URL_BASE')
        username=env('REMOTE_ARCHIVE_USERNAME')
        password=env('REMOTE_ARCHIVE_PASSWORD')

    else:
        server_url=env('LOCAL_SERVER_URL')
        archive_url_base=env('LOCAL_ARCHIVE_URL_BASE')
        username=env('LOCAL_ARCHIVE_USERNAME')
        password=env('LOCAL_ARCHIVE_PASSWORD')

    # Make sure server URL does not end with a slash.
    if server_url.endswith('/'):
        server_url = server_url[:-1]

    # Make sure archive URL base starts and ends with a slash.
    if not archive_url_base.startswith('/'):
        archive_url_base = '/' + archive_url_base
    if not archive_url_base.endswith('/'):
        archive_url_base += '/'

    archive_url = server_url + archive_url_base

    return Bunch(
        server_url=server_url,
        archive_url_base=archive_url_base,
        archive_url=archive_url,
        username=username,
        password=password)


def _get_aws_settings():
    return Bunch(
        access_key_id=env('AWS_ACCESS_KEY_ID'),
        secret_access_key=env('AWS_SECRET_ACCESS_KEY'),
        region_name=env('AWS_REGION_NAME'),
        s3_clip_bucket_name=env('AWS_S3_CLIP_BUCKET_NAME'),
        s3_clip_folder_path=env('AWS_S3_CLIP_FOLDER_PATH'))


app_settings = Bunch(
    archive_remote=_ARCHIVE_REMOTE,
    logging_level=_LOGGING_LEVEL,
    station_names=_STATION_NAMES,
    station_time_zone=_STATION_TIME_ZONE,
    old_bird_clip_device_data=_get_old_bird_clip_device_data(),
    detector_names=_DETECTOR_NAMES,
    paths=_get_paths(_STATION_NAMES, _DETECTOR_NAMES),
    clip_file_wait_period=_CLIP_FILE_WAIT_PERIOD,
    clip_file_retirement_wait_period=_CLIP_FILE_RETIREMENT_WAIT_PERIOD,
    vesper=_get_vesper_settings())

if _ARCHIVE_REMOTE:
    app_settings.aws=_get_aws_settings()
