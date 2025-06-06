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

_METADATA_DETECTOR_NAME = 'Old Bird Dickcissel Detector 1.0'

_RECORDING_START_TIME = Time(hour=21)
_RECORDING_DURATION = 8             # hours

_AUDIO_FILE_NAME_EXTENSION = '.wav'
_METADATA_FILE_NAME_EXTENSION = '.json'

_TIME_ZONE_OFFSET_LENGTH = 6
_UTC = ZoneInfo('UTC')


class OldBirdClipConverter(LinearGraph):


    def _create_processors(self):

        s = self.settings

        settings = Bunch(
            dir_path=s.source_clip_dir_path,
            file_name_re=_CLIP_FILE_NAME_RE,
            recursive=False,
            file_wait_period=s.clip_file_wait_period)
        lister = FileLister(settings, self)

        paths = s.station_paths.detectors[_DETECTOR_NAME]
        settings = Bunch(
            station_name=s.station_name,
            recorder_name=s.recorder_name,
            mic_output_name=s.mic_output_name,
            station_time_zone=s.station_time_zone,
            destination_dir_path=paths.incoming_clip_dir_path,
            clip_classification=s.clip_classification)
        mover = _ClipFileMover(settings, self)

        return lister, mover


class _ClipFileMover(SimpleSink):


    def _process_item(self, audio_file, finished):

        _logger.info(
            f'Processor "{self.path}" processing file "{audio_file.path}"...')

        s = self.settings

        # Get clip start time and serial number from audio file name.
        match = audio_file.name_match
        clip_start_time = _get_clip_start_time(match, s.station_time_zone)
        clip_serial_num = int(match.group('num'))

        # Get clip length and sample rate from audio file.
        with wave.open(str(audio_file.path), 'rb') as wave_reader:
            clip_length = wave_reader.getnframes()
            sample_rate = wave_reader.getframerate()
        
        # Get recording start time and length.
        recording_start_time = \
            _get_recording_start_time(clip_start_time, s.station_time_zone)
        recording_length = int(round(_RECORDING_DURATION * 3600 * sample_rate))

        # Get clip annotations.
        if s.clip_classification is None:
            clip_annotations = {}
        else:
            clip_annotations = {
                'Classification': s.clip_classification
            }

        # Get metadata.
        metadata = create_clip_metadata(
            s.station_name, s.recorder_name, s.mic_output_name,
            recording_start_time, recording_length, sample_rate,
            _METADATA_DETECTOR_NAME, clip_start_time, clip_serial_num,
            clip_length, clip_annotations)

        # Get metadata file path.
        file_name_stem = _get_clip_file_name_stem(
            s.station_name, clip_start_time, clip_serial_num)
        metadata_file_name = f'{file_name_stem}{_METADATA_FILE_NAME_EXTENSION}'
        metadata_file_path = s.destination_dir_path / metadata_file_name

        # Create metadata file parent directories if needed.
        try:
            metadata_file_path.parent.mkdir(
                mode=0o755, parents=True, exist_ok=True)
        except Exception as e:
            raise ArchiverError(
                f'Processor "{self.path}" could not create one or more '
                f'parent directories for clip metadata file '
                f'"{metadata_file_path}". Error message was: {e}')

        # Write metadata file.
        with open(metadata_file_path, 'wt') as file:
            json.dump(metadata, file, indent=4)

        new_audio_file_path = \
            metadata_file_path.with_suffix(_AUDIO_FILE_NAME_EXTENSION)
        
        try:
            audio_file.path.rename(new_audio_file_path)
        except Exception as e:
            raise ArchiverError(
                f'Processor "{self.path}" could not move file '
                f'"{audio_file.path}" to "{new_audio_file_path}". '
                f'Error message was: {e}')


def _get_clip_start_time(match, station_time_zone):

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
        year, month, day, hour, minute, second, tzinfo=station_time_zone)

    return start_time.astimezone(_UTC)


def _get_clip_file_name_stem(station_name, start_time, serial_num):
    start_time_text = start_time.strftime('%Y-%m-%d_%H.%M.%S.000_Z')
    return f'{station_name}_{start_time_text}_{serial_num:02d}'


def _get_recording_start_time(clip_start_time, station_time_zone):

    dt = clip_start_time.astimezone(station_time_zone)

    date = dt.date()
    if dt.hour < 12:
        date -= TimeDelta(days=1)

    dt = DateTime.combine(date, _RECORDING_START_TIME, station_time_zone)

    return dt.astimezone(_UTC)


def create_clip_metadata(
        station_name, recorder_name, mic_output_name, recording_start_time,
        recording_length, sample_rate, detector_name, clip_start_time,
        clip_serial_num, clip_length, clip_annotations):

    # Prepare recording metadata.
    start_time = _format_start_time(recording_start_time)
    recordings = [
        {
            'station': station_name,
            'recorder': recorder_name,
            'mic_outputs': [mic_output_name],
            'start_time': start_time,
            'length': recording_length,
            'sample_rate': sample_rate
        }
    ]

    # Prepare clip metadata.
    start_time = _format_start_time(clip_start_time, timespec='milliseconds')
    clips = [{
        'station': station_name,
        'mic_output': mic_output_name,
        'detector': detector_name,
        'start_time': start_time,
        'serial_num': clip_serial_num,
        'length': clip_length,
        'annotations': clip_annotations
    }]

    # Return all metadata.
    return {
        'recordings': recordings,
        'clips': clips
    }


def _format_start_time(start_time, sep=' ', **kwargs):
    start_time = start_time.isoformat(sep=sep, **kwargs)
    return start_time[:-_TIME_ZONE_OFFSET_LENGTH] + f'{sep}Z'
