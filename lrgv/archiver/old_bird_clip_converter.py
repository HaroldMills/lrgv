from datetime import (
    datetime as DateTime, time as Time, timedelta as TimeDelta)
from zoneinfo import ZoneInfo
import json
import logging
import wave

from lrgv.archiver.archiver_error import ArchiverError
from lrgv.archiver.file_lister import FileLister
from lrgv.dataflow import LinearGraph, SimpleSink
from lrgv.util.bunch import Bunch


_logger = logging.getLogger(__name__)


_DETECTOR_NAME = 'Dick'

_CLIP_FILE_NAME_RE = (
    r'^'
    f'{_DETECTOR_NAME}_'
    r'(?P<year>\d\d\d\d)-(?P<month>\d\d)-(?P<day>\d\d)'
    r'_'
    r'(?P<hour>\d\d)\.(?P<minute>\d\d)\.(?P<second>\d\d)'
    r'_'
    r'(?P<num>\d\d)'
    r'\.(?:wav|WAV)'
    r'$')

_RECORDING_START_TIME = Time(hour=21)
_RECORDING_DURATION = 8             # hours

_SENSOR_NAME_FORMAT = '{station_name} 21c'
_TIME_ZONE_OFFSET_LENGTH = 6
_METADATA_DETECTOR_NAME = 'Old Bird Dickcissel Detector 1.0'
_CLIP_CLASSIFICATION = 'Call.DICK'

_AUDIO_FILE_NAME_EXTENSION = '.wav'
_METADATA_FILE_NAME_EXTENSION = '.json'

_US_CENTRAL = ZoneInfo('US/Central')
_UTC = ZoneInfo('UTC')


class OldBirdClipConverter(LinearGraph):


    def _create_processors(self):

        s = self.settings

        name = f'{s.station_name} Old Bird Clip Lister'
        settings = Bunch(
            dir_path=s.station_paths.station_dir_path,
            file_name_re=_CLIP_FILE_NAME_RE,
            file_wait_period=s.clip_file_wait_period)
        lister = FileLister(name, settings)

        name = f'{s.station_name} Old Bird Clip Mover'
        paths = s.station_paths.detectors[_DETECTOR_NAME]
        settings = Bunch(
            station_name=s.station_name,
            destination_dir_path=paths.incoming_clip_dir_path)
        mover = _ClipFileMover(name, settings)

        return lister, mover


class _ClipFileMover(SimpleSink):


    def _process_item(self, audio_file, finished):

        _logger.info(f'{self.name} processing file "{audio_file.path}"...')

        s = self.settings

        # Get clip start time and serial number from audio file name.
        match = audio_file.name_match
        clip_start_time = _get_clip_start_time(match)
        clip_serial_num = int(match.group('num'))

        # Get clip length and sample rate from audio file.
        with wave.open(str(audio_file.path), 'rb') as wave_reader:
            clip_length = wave_reader.getnframes()
            sample_rate = wave_reader.getframerate()
        
        # Get recording start time and length.
        recording_start_time = _get_recording_start_time(clip_start_time)
        recording_length = int(round(_RECORDING_DURATION * 3600 * sample_rate))

        # Get clip annotations.
        clip_annotations = {}
        # clip_annotations = {
        #     'Classification': _CLIP_CLASSIFICATION
        # }

        # Get metadata.
        metadata = create_clip_metadata(
            s.station_name, recording_start_time, recording_length,
            sample_rate, _METADATA_DETECTOR_NAME, clip_start_time,
            clip_serial_num, clip_length, clip_annotations)

        # Get metadata file path.
        file_name_stem = _get_clip_file_name_stem(
            s.station_name, clip_start_time, clip_serial_num)
        metadata_file_name = f'{file_name_stem}{_METADATA_FILE_NAME_EXTENSION}'
        metadata_file_path = s.destination_dir_path / metadata_file_name

        # Write metadata file.
        with open(metadata_file_path, 'wt') as file:
            json.dump(metadata, file, indent=4)

        new_audio_file_path = \
            metadata_file_path.with_suffix(_AUDIO_FILE_NAME_EXTENSION)
        
        try:
            audio_file.path.rename(new_audio_file_path)
        except Exception as e:
            raise ArchiverError(
                f'Old Bird "{self.name}" could not move file '
                f'"{audio_file.path}" to "{new_audio_file_path}". '
                f'Error message was: {e}')


def _get_clip_start_time(match):

    group = match.group

    def get(field_name):
        return int(group(field_name))

    year = get('year')
    month = get('month')
    day = get('day')
    hour = get('hour')
    minute = get('minute')
    second = get('second')

    start_time = DateTime(
        year, month, day, hour, minute, second, tzinfo=_US_CENTRAL)

    return start_time.astimezone(_UTC)


def _get_clip_file_name_stem(station_name, start_time, serial_num):
    start_time_text = start_time.strftime('%Y-%m-%d_%H.%M.%S.000_Z')
    return f'{station_name}_{start_time_text}_{serial_num:02d}'


def _get_recording_start_time(clip_start_time):

    dt = clip_start_time.astimezone(_US_CENTRAL)

    date = dt.date()
    if dt.hour < 12:
        date -= TimeDelta(days=1)

    dt = DateTime.combine(date, _RECORDING_START_TIME, _US_CENTRAL)

    return dt.astimezone(_UTC)


def create_clip_metadata(
        station_name, recording_start_time, recording_length, sample_rate,
        detector_name, clip_start_time, clip_serial_num, clip_length,
        clip_annotations):

    # Prepare recording metadata.
    start_time = _format_start_time(recording_start_time)
    recording_name = f'{station_name} {start_time}'
    recordings = {
        recording_name: {
            'sensors': station_name,
            'start_time': start_time,
            'length': recording_length,
            'sample_rate': sample_rate
        }
    }

    # Prepare recording sensor metadata.
    sensor_name = _SENSOR_NAME_FORMAT.format(station_name=station_name)
    recording_sensors = {
        station_name: [sensor_name]
    }

    # Prepare clip metadata.
    start_time = _format_start_time(clip_start_time, timespec='milliseconds')
    clips = [{
        'recording': recording_name,
        'sensor': sensor_name,
        'detector': detector_name,
        'start_time': start_time,
        'serial_num': clip_serial_num,
        'length': clip_length,
        'annotations': clip_annotations
    }]

    # Return all metadata.
    return {
        'recordings': recordings,
        'recording_sensors': recording_sensors,
        'clips': clips
    }


def _format_start_time(start_time, sep=' ', **kwargs):
    start_time = start_time.isoformat(sep=sep, **kwargs)
    return start_time[:-_TIME_ZONE_OFFSET_LENGTH] + f'{sep}Z'
