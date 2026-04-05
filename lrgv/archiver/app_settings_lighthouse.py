from datetime import time as Time
from pathlib import Path
from zoneinfo import ZoneInfo
import logging

from environs import Env

from lrgv.util.bunch import Bunch


# App mode, either 'Test' or 'Production'.
_MODE = 'Test'
# _MODE = 'Production'

_PROJECT_NAME = 'Lighthouse'

_ROOT_DATA_DIR_PATH = Path(
    '/Users/harold/Desktop/NFC/Data/Old Bird/Lighthouse/2026')

_ALL_STATION_NAMES = (
    'BBBO',
    'Barker',
    'Golden Hill',
    'Hamlin Beach',
    'Hilton',
    'Kendall',
    'Lakeside',
    'Lyndonville',
    'Newfane',
    'Station 1',
    'Station 5',
    'Wilson',
)

if _MODE == 'Test':
    _TESTBED_DIR_PATH = _ROOT_DATA_DIR_PATH / 'Archiver Testbed'
    _ARCHIVE_DIR_PATH = _TESTBED_DIR_PATH / 'Vesper Archive'
    _STATION_DATA_DIR_PATH = _TESTBED_DIR_PATH / 'Station Data'
    _ARCHIVER_DATA_DIR_PATH = _TESTBED_DIR_PATH / 'Archiver Data'
    _STATION_NAMES = ('Lyndonville', 'Station 5')

elif _MODE == 'Production':
    _ARCHIVE_DIR_PATH = None
    _STATION_DATA_DIR_PATH = _ROOT_DATA_DIR_PATH / 'Synced Station Data'
    _ARCHIVER_DATA_DIR_PATH = _ROOT_DATA_DIR_PATH / 'Archiver Data'
    _STATION_NAMES = (
        'BBBO', 'Kendall', 'Lyndonville', 'Station 1', 'Station 5', 'Wilson')

_ARCHIVE_REMOTE = _ARCHIVE_DIR_PATH is None

_STATION_TIME_ZONE = ZoneInfo('US/Eastern')

_LOG_FILE_PATH = None
# _LOG_FILE_PATH = _STATION_DATA_DIR_PATH / 'archive_clips.log'

_LOGGING_LEVEL = logging.INFO

_RECORDER_NAMES = ('Vesper Recorder',)

_PROCESS_OLD_BIRD_CLIPS = True
_DELETE_OLD_BIRD_CLIPS = False
_OLD_BIRD_SHORT_DETECTOR_NAME = 'Tseep'
_OLD_BIRD_FULL_DETECTOR_NAME = 'Old Bird Tseep Detector 1.0'
_OLD_BIRD_CLIP_FILE_NAME_RE = (
    r'^'
    f'{_OLD_BIRD_SHORT_DETECTOR_NAME}_'
    r'(?P<year>\d\d\d\d)-(?P<month>\d\d)-(?P<day>\d\d)'
    r'_'
    r'(?P<hour>\d\d)\.(?P<minute>\d\d)\.(?P<second>\d\d)'
    r'_'
    r'(?P<num>\d\d)'
    r'\.(?:wav|WAV)'
    r'$')
_OLD_BIRD_DETECTOR_START_TIME = Time(hour=21)
_OLD_BIRD_DETECTOR_RUN_TIME = 8           # hours

_NON_OLD_BIRD_DETECTOR_NAMES = ('Nighthawk',)

_FILE_WAIT_PERIOD = 30                  # seconds

_SECRET_FILE_PATH = Path(__file__).parent / 'secrets/secrets_lighthouse.env'


env = Env()
env.read_env(_SECRET_FILE_PATH)


def _get_detector_names():
    if _PROCESS_OLD_BIRD_CLIPS and not _DELETE_OLD_BIRD_CLIPS:
        return (_OLD_BIRD_SHORT_DETECTOR_NAME, *_NON_OLD_BIRD_DETECTOR_NAMES)
    else:
        return _NON_OLD_BIRD_DETECTOR_NAMES


def _get_old_bird_clip_device_data():

    """
    Gets mapping from station name to (recorder name, mic output name) pair
    for Old Bird detector clips.
    """

    def get_device_data(station_num):
        detector_name = f'{_OLD_BIRD_SHORT_DETECTOR_NAME}-r'
        recorder_name = f'{detector_name} {station_num}'
        mic_output_name = f'21c {station_num} {detector_name} Output'
        return (recorder_name, mic_output_name)
    
    return dict(
        (n, get_device_data(i))
        for i, n in enumerate(_ALL_STATION_NAMES))
    

def _get_paths(station_names, recorder_names, detector_names):


    def get_synced_station_dir_path(station_name):
        station_dir_name = f'{_PROJECT_NAME} - {station_name}'
        return _STATION_DATA_DIR_PATH / station_dir_name
    

    def get_archiver_station_dir_path(station_name):
        return _ARCHIVER_DATA_DIR_PATH / station_name
    

    def get_recorder_paths(station_name, recorder_name):
        
        def get_recorder_dir_path(station_dir_path):
            return station_dir_path / 'Recordings' / recorder_name
        
        station_dir_path = get_synced_station_dir_path(station_name)
        synced_dir_path = get_recorder_dir_path(station_dir_path)

        station_dir_path = get_archiver_station_dir_path(station_name)
        archiver_dir_path = get_recorder_dir_path(station_dir_path)
        
        return Bunch(
            synced_recording_dir_path=synced_dir_path / 'Incoming',
            incoming_recording_dir_path=archiver_dir_path / 'Incoming',
            archived_recording_dir_path=archiver_dir_path / 'Archived')
    

    def get_detector_paths(station_name, detector_name):

        def get_detector_dir_path(station_dir_path):
            return station_dir_path / 'Clips' / detector_name
        
        station_dir_path = get_synced_station_dir_path(station_name)
        synced_dir_path = get_detector_dir_path(station_dir_path)

        station_dir_path = get_archiver_station_dir_path(station_name)
        archiver_dir_path = get_detector_dir_path(station_dir_path)

        return Bunch(
            synced_clip_dir_path=synced_dir_path / 'Incoming',
            incoming_clip_dir_path=archiver_dir_path / 'Incoming',
            created_clip_dir_path=archiver_dir_path / 'Created',
            archived_clip_dir_path=archiver_dir_path / 'Archived')
    

    def get_station_paths(station_name, recorder_names, detector_names):

        synced_station_dir_path = get_synced_station_dir_path(station_name)

        recorder_paths = {
            recorder_name: get_recorder_paths(station_name, recorder_name)
            for recorder_name in recorder_names
        }
        
        detector_paths = {
            detector_name: get_detector_paths(station_name, detector_name)
            for detector_name in detector_names
        }

        return Bunch(
            synced_station_dir_path=synced_station_dir_path,
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
    
    # clips
    process_old_bird_clips=_PROCESS_OLD_BIRD_CLIPS,
    delete_old_bird_clips=_DELETE_OLD_BIRD_CLIPS,
    old_bird_short_detector_name=_OLD_BIRD_SHORT_DETECTOR_NAME,
    old_bird_full_detector_name=_OLD_BIRD_FULL_DETECTOR_NAME,
    old_bird_clip_file_name_re=_OLD_BIRD_CLIP_FILE_NAME_RE,
    old_bird_detector_start_time=_OLD_BIRD_DETECTOR_START_TIME,
    old_bird_detector_run_time=_OLD_BIRD_DETECTOR_RUN_TIME,
    old_bird_clip_device_data=_get_old_bird_clip_device_data(),
    detector_names=_detector_names,
    clip_file_wait_period=_FILE_WAIT_PERIOD,
    
    # paths
    paths=_get_paths(_STATION_NAMES, _RECORDER_NAMES, _detector_names),

    # Vesper server
    vesper=_get_vesper_settings()

)

if _ARCHIVE_REMOTE:
    app_settings.aws=_get_aws_settings()
