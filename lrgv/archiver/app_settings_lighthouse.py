from pathlib import Path
from zoneinfo import ZoneInfo
import logging

from environs import Env

from lrgv.util.bunch import Bunch


# App mode, either 'Test' or 'Production'.
# _MODE = 'Test'
_MODE = 'Production'

_PROJECT_NAME = 'Lighthouse'

_ROOT_DATA_DIR_PATH = Path(
    '/Users/harold/Desktop/NFC/Data/Old Bird/Lighthouse/2025')

_ALL_STATION_NAMES = (
    'Barker',
    'Lyndonville',
    'Newfane',
    'Station 5',
    'Wilson'
)

if _MODE == 'Test':
    _TEST_DATA_DIR_PATH = _ROOT_DATA_DIR_PATH / 'Archiver Test Data'
    _ARCHIVE_DIR_PATH = _TEST_DATA_DIR_PATH / 'Test Archive'
    _STATION_DATA_DIR_PATH = _TEST_DATA_DIR_PATH / 'Test Station Data'
    _STATION_NAMES = ('Barker', 'Newfane')


elif _MODE == 'Production':
    _ARCHIVE_DIR_PATH = None
    _STATION_DATA_DIR_PATH = _ROOT_DATA_DIR_PATH / 'Station Data'
    _STATION_NAMES = _ALL_STATION_NAMES

_ACTIVE_DATA_DIR_PATH = _STATION_DATA_DIR_PATH / 'Active'
_RETIRED_DATA_DIR_PATH = _STATION_DATA_DIR_PATH / 'Retired'

_ARCHIVE_REMOTE = _ARCHIVE_DIR_PATH is None

_STATION_TIME_ZONE = ZoneInfo('US/Eastern')

_LOG_FILE_PATH = None
# _LOG_FILE_PATH = _STATION_DATA_DIR_PATH / 'archive_clips.log'

_LOGGING_LEVEL = logging.INFO

_RECORDER_NAMES = ('Vesper Recorder',)

_PROCESS_OLD_BIRD_CLIPS = False
_DELETE_OLD_BIRD_CLIPS = True
_OLD_BIRD_DETECTOR_NAME = 'Dick'
_NON_OLD_BIRD_DETECTOR_NAMES = ('Nighthawk',)

_FILE_WAIT_PERIOD = 60                  # seconds
# _FILE_RETIREMENT_WAIT_PERIOD = 0        # seconds
# _FILE_RETIREMENT_WAIT_PERIOD = 60       # seconds
_FILE_RETIREMENT_WAIT_PERIOD = 86400    # seconds

_SECRET_FILE_PATH = Path(__file__).parent / 'secrets/secrets_lighthouse.env'


env = Env()
env.read_env(_SECRET_FILE_PATH)


def _get_detector_names():
    if _PROCESS_OLD_BIRD_CLIPS and not _DELETE_OLD_BIRD_CLIPS:
        return (_OLD_BIRD_DETECTOR_NAME, *_NON_OLD_BIRD_DETECTOR_NAMES)
    else:
        return _NON_OLD_BIRD_DETECTOR_NAMES


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
    

def _get_paths(station_names, recorder_names, detector_names):


    def get_recorder_paths(
            active_recording_dir_path, retired_recording_dir_path,
            recorder_name):

        active_dir_path = active_recording_dir_path / recorder_name
        retired_dir_path = retired_recording_dir_path / recorder_name
        
        return Bunch(
            incoming_recording_dir_path=active_dir_path / 'Incoming',
            archived_recording_dir_path=active_dir_path / 'Archived',
            retired_recording_dir_path=retired_dir_path / 'Archived')


    def get_detector_paths(
            active_clip_dir_path, retired_clip_dir_path, detector_name):

        active_dir_path = active_clip_dir_path / detector_name
        retired_dir_path = retired_clip_dir_path / detector_name

        return Bunch(
            incoming_clip_dir_path=active_dir_path / 'Incoming',
            created_clip_dir_path=active_dir_path / 'Created',
            archived_clip_dir_path=active_dir_path / 'Archived',
            retired_clip_dir_path=retired_dir_path / 'Archived')


    def get_station_paths(station_name, recorder_names, detector_names):

        station_dir_name = f'{_PROJECT_NAME} - {station_name}'
        station_dir_path = _ACTIVE_DATA_DIR_PATH / station_dir_name

        active_recording_dir_path = station_dir_path / 'Recordings'
        retired_recording_dir_path = \
            _RETIRED_DATA_DIR_PATH / station_name / 'Recordings'
        recorder_paths = {
            recorder_name: get_recorder_paths(
                active_recording_dir_path, retired_recording_dir_path,
                recorder_name)
            for recorder_name in recorder_names
        }
        
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
            recorders=recorder_paths,
            detectors=detector_paths)

    station_paths = {
        station_name: 
            get_station_paths(station_name, recorder_names, detector_names)
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


_detector_names = _get_detector_names()

app_settings = Bunch(

    project_name=_PROJECT_NAME,
    archive_remote=_ARCHIVE_REMOTE,
    logging_level=_LOGGING_LEVEL,

    # stations
    station_names=_STATION_NAMES,
    station_time_zone=_STATION_TIME_ZONE,

    # recordings
    recorder_names=_RECORDER_NAMES,
    recording_file_wait_period=_FILE_WAIT_PERIOD,
    recording_file_retirement_wait_period=_FILE_RETIREMENT_WAIT_PERIOD,

    # clips
    old_bird_clip_device_data=_get_old_bird_clip_device_data(),
    process_old_bird_clips=_PROCESS_OLD_BIRD_CLIPS,
    delete_old_bird_clips=_DELETE_OLD_BIRD_CLIPS,
    detector_names=_detector_names,
    clip_file_wait_period=_FILE_WAIT_PERIOD,
    clip_file_retirement_wait_period=_FILE_RETIREMENT_WAIT_PERIOD,

    # paths
    paths=_get_paths(_STATION_NAMES, _RECORDER_NAMES, _detector_names),

    # Vesper server
    vesper=_get_vesper_settings()

)

if _ARCHIVE_REMOTE:
    app_settings.aws=_get_aws_settings()
