"""
Script that runs the Nighthawk NFC detector on recording files
from one night and creates an audio file and a metadata file for
each resulting detection.

The script has two required command line arguments, a recording
directory path and a clip directory path. It also has an optional
third argument, the date of the night for which to run the detector.
The third argument defaults to yesterday's date.

Each LRGV station laptop runs this script every morning after the
previous night's recording completes to process the recording. Each
station laptop's clip directory is synced with one or more remote
computers via SugarSync. We run the LRGV archiver on one such
computer to put the clips into a Vesper cloud archive.
"""


# TODO: Add command line argument for Nighthawk output directory.


from collections import defaultdict
from datetime import (
    date as Date, datetime as DateTime, timedelta as TimeDelta)
from pathlib import Path
from zoneinfo import ZoneInfo
import csv
import json
import logging
import sys
import wave

from lrgv.util.bunch import Bunch
import lrgv.util.conda_utils as conda_utils
import lrgv.util.logging_utils as logging_utils


logger = logging.getLogger(__name__)


ROOT_DIR_PATH = Path(__file__).parent
TAXON_MAPPING_FILE_PATH = ROOT_DIR_PATH / 'species_code_mapping.json'
LOG_FILE_NAME = 'run_nighthawk.log'
WAVE_FILE_NAME_EXTENSION = '.wav'
CSV_FILE_NAME_EXTENSION = '.csv'
JSON_FILE_NAME_EXTENSION = '.json'
RECORDING_FILE_STATION_NAMES = {
    'DHS': 'Donna',
    'DOHS': 'Donna',
    'HHSS': 'Harlingen',
    'PIJHS': 'Port Isabel',
    'RBMS': 'Roma RBMS',
    'RHHS': 'Rio Hondo',
    'ROHS': 'Roma HS',
}
STATION_TIME_ZONE = ZoneInfo('US/Central')
UTC_TIME_ZONE = ZoneInfo('UTC')
TIME_ZONE_OFFSET_LENGTH = 6
SENSOR_NAME_FORMAT = '{station_name} 21c'
DETECTOR_NAME = 'Nighthawk 0.3.0 80'


def main():

    log_file_path = Path.cwd() / LOG_FILE_NAME
    logging_utils.configure_logging(logging.INFO, log_file_path)

    # Get recording and clip directory paths.
    recording_dir_path, clip_dir_path, date = parse_args(sys.argv)
    logger.info(f'Recording directory path is "{recording_dir_path}".')
    logger.info(f'Clip directory path is "{clip_dir_path}".')

    taxon_mapping = get_taxon_mapping(TAXON_MAPPING_FILE_PATH)

    files = get_recording_files(recording_dir_path, date)

    log_file_count(len(files), date)

    for file in files:

        logger.info(f'Processing recording file "{file.path}"...')

        try:
            result = run_nighthawk_on_file(file)
        except Exception as e:
            logger.warning(
                f'Attempt to run Nighthawk on recording file '
                f'"{file.path}" raised exception with message: {e}')
            
        if result:

            try:
                process_detections(file, taxon_mapping, clip_dir_path)
            except Exception as e:
                logger.warning(
                    f'Attempt to process Nighthawk detections for '
                    f'recording file "{file.path}" raised exception with '
                    f'message: {e}')
 

def parse_args(args):

    if len(args) != 3 and len(args) != 4:
        logger.critical(f'Bad script arguments: {args}')
        logger.critical(
            'Usage: run_nighthawk <recording_dir_path> <clip_dir_path> '
            '[<date>]')
        sys.exit(1)

    recording_dir_path = Path(args[1])

    if not recording_dir_path.exists():
        logger.critical(
            f'Specified recording directory "{recording_dir_path}" does '
            f'not exist.')
        sys.exit(1)

    clip_dir_path = Path(args[2])

    if not clip_dir_path.exists():
        logger.critical(
            f'Specified clip directory "{clip_dir_path}" does not exist.')
        sys.exit(1)

    if len(args) == 4:
        try:
            date = Date.fromisoformat(args[3])
        except Exception:
            logger.critical(f'Bad date "{args[3]}".')
            sys.exit(1)
    else:
        date = Date.fromordinal(Date.today().toordinal() - 1)

    return recording_dir_path, clip_dir_path, date


def get_taxon_mapping(file_path):

    if file_path.exists():

        try:
            with open(file_path) as json_file:
                return json.load(json_file)
            
        except Exception as e:
            logger.critical(
                f'Attempt to load taxon mapping "{file_path}" raised '
                f'exception with message: {e}')
            sys.exit(1)

    else:
        logger.info(
            f'Taxon mapping file "{file_path}" does not exist. Script '
            f'will not map any taxon names.')
        return {}
    

def get_recording_files(recording_dir_path, date):

    noon = DateTime(
        date.year, date.month, date.day, 12, tzinfo=STATION_TIME_ZONE)

    files = []

    for file_path in recording_dir_path.glob('*.wav'):
        file = parse_recording_file_path(file_path)
        if file is not None and file.start_time >= noon:
            files.append(file)

    return files


def parse_recording_file_path(path):

    name = path.name

    parts = name[:-4].split('-', 1)

    if len(parts) != 2:
        logger.info(
            f'Could not parse audio file name "{name}". File will be '
            f'ignored.')
        return None
    
    station_name, start_time = parts

    try:
        start_time = DateTime.strptime(start_time, '%Y-%m-%d-%H-%M-%S')
    except Exception:
        logger.info(
            f'Could not parse start time of audio file name "{name}". '
            f'File will be ignored.')
        return None
    
    # Get UTC start time.
    start_time = start_time.replace(tzinfo=STATION_TIME_ZONE)
    start_time = start_time.astimezone(UTC_TIME_ZONE)
    
    file = Bunch()
    file.path = path
    file.station_name = station_name
    file.start_time = start_time

    return file


def log_file_count(count, date):

    if count == 0:
        text = "no recording files"
    elif count == 1:
        text = "one recording file"
    else:
        text = f'{count} recording files'

    logger.info(f'Found {text} for date {date}.')


def run_nighthawk_on_file(file):

    # return True

    logger.info(f'    Running Nighthawk...')
    
    module_name = 'nighthawk.run_nighthawk'
    
    # Build list of command line arguments.
    args = [str(file.path)]
    
    environment_name = f'nighthawk-0.3.0'
    
    try:
        results = conda_utils.run_python_script(
            module_name, args, environment_name)
    
    except Exception as e:

        logger.error(
            f'    Could not run Nighthawk in Conda environment '
            f'"{environment_name}". Error message was: {e}')
        
        return False
    
    if results.returncode != 0:
        # detector process completed abnormally.
        
        logger.error(
            f'    Nighthawk process completed abnormally with return '
            f'code {results.returncode}. No clips will be created.')
        
        log_process_output_streams(results)

        return False
    
    else:
        # detector process completed normally
        
        logger.info('    Nighthawk process completed normally.')

        log_process_output_streams(results)

        return True


def log_process_output_streams(results):
    log_process_output_stream(results.stdout, 'standard output')
    log_process_output_stream(results.stderr, 'standard error')
    

def log_process_output_stream(stream_text, stream_name):
    
    if len(stream_text) == 0:
        logger.info(f'    Nighthawk process {stream_name} was empty.')
    
    else:
        logger.info(f'    Nighthawk process {stream_name} was:')
        lines = stream_text.strip().splitlines()
        for line in lines:
            logger.info(f'        {line}')


def process_detections(recording_file, taxon_mapping, clip_dir_path):

    detection_file_path = get_detection_file_path(recording_file.path)
    logger.info(f'    Processing detection file "{detection_file_path}"...')

    station_name = recording_file.station_name
    station_name = RECORDING_FILE_STATION_NAMES.get(station_name, station_name)

    # Get recording sensors.
    sensor_name = SENSOR_NAME_FORMAT.format(station_name=station_name)
    recording_sensors = {
        station_name: [sensor_name]
    } 

    # Note that in the following we open the detection CSV file twice,
    # once so we can read it using a `csv.DictReader` and a second time
    # so that we can read it as a regular text file. This allows us
    # to read CSV file values by column name as well as read whole
    # CSV file lines and write them unaltered to the per-clip output
    # CSV files.
    with wave.open(str(recording_file.path), 'rb') as wave_reader, \
            open(detection_file_path, newline='') as csv_file, \
            open(detection_file_path, newline='') as text_file:
    
        clip_counts = defaultdict(int)

        csv_reader = csv.DictReader(csv_file)

        # Skip CSV file header.
        text_file.readline()

        # Get recording metadata.
        start_time = format_start_time(recording_file.start_time)
        recording_name = f'{station_name} {start_time}'
        length = wave_reader.getnframes()
        sample_rate = wave_reader.getframerate()
        recordings = {
            recording_name: {
                'sensors': station_name,
                'start_time': start_time,
                'length': length,
                'sample_rate': sample_rate
            }
        }
            
        for detection in csv_reader:

            # Get detection start and end offsets.
            start_offset = float(detection['start_sec'])
            end_offset = float(detection['end_sec'])

            # Get clip file name stem.
            start_delta = TimeDelta(seconds=start_offset)
            clip_start_time = recording_file.start_time + start_delta
            start_time = format_start_time(
                clip_start_time, sep='_', timespec='milliseconds')
            start_time = start_time.replace(':', '.')
            key = (station_name, start_time)
            clip_num = clip_counts[key]
            clip_file_name_stem = f'{station_name}_{start_time}_{clip_num:02}'
            clip_audio_file_path = create_file_path(
                clip_dir_path, clip_file_name_stem, WAVE_FILE_NAME_EXTENSION)
            clip_counts[key] += 1
 
            create_clip_audio_file(
                clip_audio_file_path, wave_reader, start_offset, end_offset)

            # Get file line from which `detection` was created.
            csv_line = text_file.readline().strip()

            duration = end_offset - start_offset
            start_time = \
                format_start_time(clip_start_time, timespec='milliseconds')
            length = s2f(duration, sample_rate)

            annotations = get_clip_annotations(
                detection, taxon_mapping, csv_line)

            clips = [{
                'recording': recording_name,
                'sensor': sensor_name,
                'detector': DETECTOR_NAME,
                'start_time': start_time,
                'length': length,
                'annotations': annotations
            }]
            
            clip_metadata = {
                'recordings': recordings,
                'recording_sensors': recording_sensors,
                'clips': clips
            }

            clip_metadata_file_path = create_file_path(
                clip_dir_path, clip_file_name_stem, JSON_FILE_NAME_EXTENSION)

            with open(clip_metadata_file_path, 'wt') as json_file:
                json.dump(clip_metadata, json_file, indent=4)


def get_detection_file_path(input_file_path):
    detection_file_name = f'{input_file_path.stem}_detections.csv'
    return input_file_path.parent / detection_file_name
    
    
def get_clip_metadata_file_path(input_file_path, clip_dir_path):
    clip_metadata_file_name = f'{input_file_path.stem}_clips.json'
    return clip_dir_path / clip_metadata_file_name
    
    
def format_start_time(start_time, sep=' ', **kwargs):
    start_time = start_time.isoformat(sep=sep, **kwargs)
    return start_time[:-TIME_ZONE_OFFSET_LENGTH] + f'{sep}Z'


def create_file_path(dir_path, file_name_stem, file_name_extension):
    file_name = file_name_stem + file_name_extension
    return dir_path / file_name


def create_clip_audio_file(file_path, wave_reader, start_offset, end_offset):

    # Get sample rate.
    sample_rate = wave_reader.getframerate()

    # Read clip audio data from recording file.
    start_index = s2f(start_offset, sample_rate)
    end_index = s2f(end_offset, sample_rate)
    length = end_index - start_index
    wave_reader.setpos(start_index)
    data = wave_reader.readframes(length)

    # Write clip audio file.
    with wave.open(str(file_path), 'wb') as wave_writer:

        channel_count = 1
        sample_size = 2
        compression_type = 'NONE'
        compression_name = 'not compressed'
        
        wave_writer.setparams((
            channel_count, sample_size, sample_rate, length,
            compression_type, compression_name))
        
        wave_writer.writeframesraw(data)


def s2f(time, sample_rate):
    return int(round(time * sample_rate))


def get_clip_annotations(detection, taxon_mapping, csv_line):

    d = detection

    species = map_taxon(d['species'], taxon_mapping)
    predicted_category = map_taxon(d['predicted_category'], taxon_mapping)

    classification = 'Call.' + predicted_category
    score = str(100 * float(d['prob']))

    return {
        'Detector Score': score,
        'Classification': classification,
        'Classifier Score': score,
        'Nighthawk Order': d['order'],
        'Nighthawk Order Probability': d['prob_order'],
        'Nighthawk Family': d['family'],
        'Nighthawk Family Probability': d['prob_family'],
        'Nighthawk Group': d['group'],
        'Nighthawk Group Probability': d['prob_group'],
        'Nighthawk Species': species,
        'Nighthawk Species Probability': d['prob_species'],
        'Nighthawk Predicted Category': predicted_category,
        'Nighthawk Probability': d['prob'],
        'Nighthawk Output File Line': csv_line,
    }


def map_taxon(taxon, taxon_mapping):
    return taxon_mapping.get(taxon, taxon)


if __name__ == '__main__':
    main()
