"""
Script that runs the Nighthawk NFC detector on Lighthouse recording
files from one night and creates an audio file and a metadata file
for each resulting detection.

The script has three required command line arguments, a recording
directory path, a Nighthawk output directory path, and a clip directory
path. It also has an optional fourth argument, the date of the night
for which to run the detector. The fourth argument defaults to yesterday's
date.

Each station laptop in the monitoring network runs this script every
morning after the previous night's recording completes to process the
recording. Each station laptop's clip directory is synced with one or
more remote computers via SugarSync. We run the clip archiver on one
such computer to put the clips into a Vesper cloud archive.
"""


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
LOG_FILE_PATH = Path.cwd() / 'run_nighthawk.log'

CSV_FILE_NAME_EXTENSION = '.csv'
AUDIO_FILE_NAME_EXTENSION = '.wav'
JSON_FILE_NAME_EXTENSION = '.json'

ZERO_SECONDS = TimeDelta(seconds=0)
ONE_DAY = TimeDelta(days=1)
STATION_TIME_ZONE = ZoneInfo('US/Eastern')
UTC_TIME_ZONE = ZoneInfo('UTC')
TIME_ZONE_OFFSET_LENGTH = 6
RECORDER_NAME_FORMAT = 'Vesper Recorder {station_num}'
MIC_OUTPUT_NAME_FORMAT = '21c {station_num} Vesper Output'
DETECTOR_NAME = 'Nighthawk 0.3.1 80'

RECORDING_FILE_STATION_NAMES = {}

STATION_NAMES = (
    'Barker',
    'Lyndonville',
    'Newfane',
    'Station 5',
    'Wilson'
)

STATION_NUMS = {n: i for i, n in enumerate(STATION_NAMES)}

INCLUDED_CLASSIFICATIONS = frozenset([
    'Call.BAWW', 'Call.CAWA', 'Call.DICK', 'Call.GRSP', 'Call.LESA', 
    'Call.UPSA'
])


def main():

    logging_utils.configure_logging(logging.INFO, LOG_FILE_PATH)

    # Get recording and clip directory paths.
    recording_dir_path, nighthawk_output_dir_path, clip_dir_path, date = \
        parse_args(sys.argv)
    logger.info(f'Recording directory path is "{recording_dir_path}".')
    logger.info(
        f'Nighthawk output directory path is "{nighthawk_output_dir_path}".')
    logger.info(f'Clip directory path is "{clip_dir_path}".')

    create_dir_if_needed(
        nighthawk_output_dir_path, 'Nighthawk output')
    
    create_dir_if_needed(clip_dir_path, 'clip')

    taxon_mapping = get_taxon_mapping(TAXON_MAPPING_FILE_PATH)

    files = get_recording_files(recording_dir_path, date)

    log_file_count(len(files), date)

    for file in files:

        logger.info(f'Processing recording file "{file.path}"...')

        try:
            result = run_nighthawk_on_file(file, nighthawk_output_dir_path)
        except Exception as e:
            logger.warning(
                f'Attempt to run Nighthawk on recording file '
                f'"{file.path}" raised exception with message: {e}')
            
        if result:

            try:
                process_detections(
                    file, taxon_mapping, nighthawk_output_dir_path,
                    clip_dir_path)
            except Exception as e:
                logger.warning(
                    f'Attempt to process Nighthawk detections for '
                    f'recording file "{file.path}" raised exception with '
                    f'message: {e}')
                
    logger.info(f'Script complete.')
 

def parse_args(args):

    if len(args) != 4 and len(args) != 5:
        logger.critical(f'Bad script arguments: {args}')
        logger.critical(
            'Usage: run_nighthawk <recording_dir_path> '
            '<nighthawk_output_dir_path> <clip_dir_path> [<date>]')
        sys.exit(1)

    recording_dir_path = Path(args[1])

    if not recording_dir_path.exists():
        logger.critical(
            f'Specified recording directory "{recording_dir_path}" does '
            f'not exist.')
        sys.exit(1)

    nighthawk_output_dir_path = Path(args[2])
    clip_dir_path = Path(args[3])

    if len(args) == 5:
        try:
            date = Date.fromisoformat(args[4])
        except Exception:
            logger.critical(f'Bad date "{args[4]}".')
            sys.exit(1)
    else:
        date = Date.fromordinal(Date.today().toordinal() - 1)

    return recording_dir_path, nighthawk_output_dir_path, clip_dir_path, date


def create_dir_if_needed(dir_path, name):

    if not dir_path.exists():

        logger.info(f'Creating {name} directory "{dir_path}"...')

        try:
            dir_path.mkdir(mode=0o755, parents=True, exist_ok=True)

        except Exception as e:
            logger.critical(
                f'Could not create directory "{dir_path}". Error message '
                f'was: {e}')
            sys.exit(1)


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
        if file is not None:
            delta = file.start_time - noon
            if delta >= ZERO_SECONDS and delta < ONE_DAY:
                files.append(file)

    return files


def parse_recording_file_path(path):

    name = path.name

    parts = name[:-4].split('_', 1)

    if len(parts) != 2:
        logger.info(
            f'Could not parse audio file name "{name}". File will be '
            f'ignored.')
        return None
    
    station_name, start_time = parts

    try:
        start_time = DateTime.strptime(start_time, '%Y-%m-%d_%H.%M.%S_Z')
    except Exception:
        logger.info(
            f'Could not parse start time of audio file name "{name}". '
            f'File will be ignored.')
        return None
    
    # Make time zone UTC.
    start_time = start_time.replace(tzinfo=UTC_TIME_ZONE)
    
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


def run_nighthawk_on_file(file, nighthawk_output_dir_path):

    # return True

    logger.info(f'    Running Nighthawk...')
    
    module_name = 'nighthawk.run_nighthawk'
    
    # Build list of command line arguments.
    args = ['--output-dir', str(nighthawk_output_dir_path), str(file.path)]
    
    environment_name = f'nighthawk-0.3.1'
    
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


def process_detections(
        recording_file, taxon_mapping, nighthawk_output_dir_path,
        clip_dir_path):

    detection_file_path = get_detection_file_path(
        recording_file.path, nighthawk_output_dir_path)
    logger.info(f'    Processing detection file "{detection_file_path}"...')

    station_name = recording_file.station_name
    key = station_name.lower()
    station_name = RECORDING_FILE_STATION_NAMES.get(key, station_name)

    station_num = STATION_NUMS[station_name]
    recorder_name = RECORDER_NAME_FORMAT.format(station_num=station_num)
    mic_output_name = MIC_OUTPUT_NAME_FORMAT.format(station_num=station_num)

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
        length = wave_reader.getnframes()
        sample_rate = wave_reader.getframerate()
        recordings = [{
            'station': station_name,
            'recorder': recorder_name,
            'mic_outputs': [mic_output_name],
            'start_time': start_time,
            'length': length,
            'sample_rate': sample_rate
        }]
            
        for detection in csv_reader:

            # Get detection start and end offsets.
            start_offset = float(detection['start_sec'])
            end_offset = float(detection['end_sec'])

            # Get clip start time.
            start_delta = TimeDelta(seconds=start_offset)
            start_time = recording_file.start_time + start_delta

            # Get clip serial number. We assign a serial number to
            # each clip to distinguish clips with the same start time.
            # The serial numbers for a given start time are zero
            # through n - 1, where n is the number of clips with that
            # start time. The combination of start time and serial
            # number is unique over all clips.
            #
            # We use the serial numbers for two purposes. First, we
            # use them to create unique clip file names. Second, the
            # Django view that creates clips in a Vesper archive uses
            # them to create unique clip start times. (The Vesper
            # archive database requires that the combination of
            # recording channel, start time, and creating processor be
            # unique across all clips. See the
            # `vesper.django.old_bird.views.ImportRecordingsAndClipsView`
            # Django view for more on this.)
            key = (station_name, start_time)
            serial_num = clip_counts[key]
            clip_counts[key] += 1
 
            # Get file line from which `detection` was created.
            csv_line = text_file.readline().strip()

            # Get clip annotations.
            annotations = get_clip_annotations(
                detection, taxon_mapping, csv_line)

            # Skip the rest of this loop body if clip's classification
            # is not included.
            classification = annotations['Classification']
            if not classification_included(classification):
                continue

            # Format start time for metadata file content.
            start_time_text = \
                format_start_time(start_time, timespec='milliseconds')
            
            # Get clip length in samples.
            duration = end_offset - start_offset
            length = s2f(duration, sample_rate)

            # Collect clip metadata for metadata file.
            clips = [{
                'station': station_name,
                'mic_output': mic_output_name,
                'detector': DETECTOR_NAME,
                'start_time': start_time_text,
                'serial_num': serial_num,
                'length': length,
                'annotations': annotations
            }]
            clip_metadata = {
                'recordings': recordings,
                'clips': clips
            }

            # Get clip file name stem.
            start_time_text = format_start_time(
                start_time, sep='_', timespec='milliseconds')
            start_time_text = start_time_text.replace(':', '.')
            clip_file_name_stem = \
                f'{station_name}_{start_time_text}_{serial_num:02}'

            # Get metadata file path.
            clip_metadata_file_path = create_file_path(
                clip_dir_path, clip_file_name_stem, JSON_FILE_NAME_EXTENSION)

            # Write metadata file.
            with open(clip_metadata_file_path, 'wt') as json_file:
                json.dump(clip_metadata, json_file, indent=4)

            # Get audio file path.
            clip_audio_file_path = create_file_path(
                clip_dir_path, clip_file_name_stem, AUDIO_FILE_NAME_EXTENSION)
            
            # Write audio file.
            create_clip_audio_file(
                clip_audio_file_path, wave_reader, start_offset, end_offset)


def get_detection_file_path(input_file_path, nighthawk_output_dir_path):
    detection_file_name = f'{input_file_path.stem}_detections.csv'
    return nighthawk_output_dir_path / detection_file_name
    
    
def get_clip_metadata_file_path(input_file_path, clip_dir_path):
    clip_metadata_file_name = f'{input_file_path.stem}_clips.json'
    return clip_dir_path / clip_metadata_file_name
    
    
def format_start_time(start_time, sep=' ', **kwargs):
    start_time = start_time.isoformat(sep=sep, **kwargs)
    return start_time[:-TIME_ZONE_OFFSET_LENGTH] + f'{sep}Z'


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


def classification_included(classification):
    return INCLUDED_CLASSIFICATIONS is None or \
        classification in INCLUDED_CLASSIFICATIONS


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



if __name__ == '__main__':
    main()
