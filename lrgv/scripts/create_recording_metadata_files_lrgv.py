"""
Script that creates Vesper recording metadata files from a CSV recording
file list for the LRGV project.

Usage:
    python create_recording_metadata_files_lrgv.py
        --input-file <input file path>
        [--output-dir <output directory path>]
        [--date <date>]
        [--start-date <start date>]
        [--end-date <end date>]

The input file should be a CSV file with a one-line header and columns for
file path, file name, channel count, sample rate in hertz, frame count,
and duration the form H:MM:SS.SSS. An example of the first two lines of such
an inputfile is:

    File Path,File Name,Channel Count,Sample Rate (Hz),Frame Count,Duration
    "/Volumes/Recordings/Alamo_2025-04-09_01.22.52_Z.wav","Alamo_2025-04-09_01.22.52_Z.wav",1,22050,783127800,9:51:56.000

The output directory is where the recording metadata files will be created.
If the output directory is not specified, it defaults to the parent
directory of the input file.

The date, start date, and end date arguments can be used to specify the
date range of recordings for which to create metadata files. The date
argument is mutually exclusive with the start date and end date arguments. If
none of these arguments are specified, the script will run for today's
date. The date, start date, and end date arguments must be either a date
of the form YYYY-MM-DD or one of the words "today", "yesterday", or
"tomorrow".

For the LRGV project, this script will typically be run each morning on
each station laptop to create metadata files for the previous night's
recordings. It may also sometimes be run manually on the archiver computer
to make sure all recordings are in the cloud archive.
"""


from argparse import ArgumentParser
from datetime import timedelta as TimeDelta
from pathlib import Path
from zoneinfo import ZoneInfo
import csv
import logging
import sys

import lrgv.util.arg_utils as arg_utils
import lrgv.util.file_utils as file_utils


# TODO: Consider making this script more flexible regarding recording
#       file name formats. It currently assumes Vesper Recorder recording
#       file names. We might want to process files with names in other
#       formats at some point, such as i-Sound Recorder files.


logger = logging.getLogger(__name__)


'''
Station data directory structure:

Apps
Clips
Recordings
    i-Sound Recorder
        Recording Files.csv
    Vesper Recorder
        Recording Files.csv
        Incoming
            Alamo_2025-07-30_07.03.18.800_Z.json

        
Example recording metadata JSON:

    "recordings": [
        {
            "station": "Alamo",
            "recorder": "Vesper Recorder 0",
            "mic_outputs": [
                "21c 0 Vesper Output"
            ],
            "start_time": "2025-07-31 01:50:09 Z",
            "length": 684961200,
            "sample_rate": 22050
        }
    ],

'''


STATION_NAMES = (
    'Alamo',
    'Donna',
    'Harlingen',
    'Port Isabel',
    'Rio Hondo',
    'Roma HS',
    'Roma RBMS',
    'Rio Grande City'
)

STATION_NUMS = {n: i for i, n in enumerate(STATION_NAMES)}

RECORDER_NAME_FORMAT = 'Vesper Recorder {}'
MIC_OUTPUT_NAME_FORMAT = '21c {} Vesper Output'

STATION_TIME_ZONE = ZoneInfo('US/Central')

ONE_DAY = TimeDelta(days=1)


def main():

    input_file_path, output_dir_path, start_date, end_date = \
        parse_args(sys.argv)

    # print(f"Input file path: {input_file_path}")
    # print(f"Output directory path: {output_dir_path}")
    # print(f"Start date: {start_date}")
    # print(f"End date: {end_date}")

    files = get_recording_files(input_file_path, start_date, end_date)

    create_recording_metadata_files(files, output_dir_path)


def parse_args(args):

    parser = create_arg_parser()

    # Parse script arguments with the parser.
    args = parser.parse_args(args[1:])

    if args.output_dir is None:
        # output dir path not specified

        # Set output dir path to parent directory of input file.
        args.output_dir = args.input_file.parent

    elif not args.output_dir.is_absolute():
        # output dir path is relative

        # Make it absolute by joining it with the parent directory of the
        # input file.
        args.output_dir = args.input_file.parent / args.output_dir

    # Perform some additional argument checks.
    try:
        start_date, end_date = arg_utils.get_start_and_end_dates(args)
    except Exception as e:
        message = f'Could not parse script arguments. Error message was: {e}'
        logger.critical(message)
        logger.critical(parser.format_help())
        sys.exit(1)

    return args.input_file, args.output_dir, start_date, end_date


def create_arg_parser():

    parser = ArgumentParser(description='Extract Nighthawk clips.')

    parser.add_argument(
        '--input-file', required=True, type=Path,
        help=(
            'Path of input file containing recording metadata. '
            'The file should be a CSV file with a one-line header and '
            'columns for file path, channel count, sample rate in Hz, '
            'frame count, and duration in the form H:MM:SS.SSS.'))

    parser.add_argument(
        '--output-dir', required=False, type=Path,
        help=(
            'Path of output directory where recording metadata files '
            'should be created. Defaults to the parent directory of '
            'the input file.'))

    arg_utils.add_date_args(
        parser,
        date_arg_help=(
            'Date of recording for which to create metadata files. '
            'This argument must be either a date of the form YYYY-MM-DD '
            'or one of the words "today", "yesterday", or "tomorrow". '
            'This argument is mutually exclusive with the --start-date '
            'and --end-date arguments. If this argument and the '
            '--start-date and --end-date arguments are not specified, '
            'the script will run for today\'s date.'),
        start_date_arg_help=(
            'Start date of recordings for which to create metadata files. '
            'This argument must be either a date of the form YYYY-MM-DD '
            'or one of the words "today", "yesterday", or "tomorrow". '
            'This argument is mutually exclusive with the --date argument.'),
        end_date_arg_help=(
            'End date of recordings for which to create metadata files. '
            'This argument must be either a date of the form YYYY-MM-DD '
            'or one of the words "today", "yesterday", or "tomorrow". '
            'This argument is mutually exclusive with the --date argument.'))
    
    return parser
    

def get_recording_files(input_file_path, start_date, end_date):

    files = []

    with open(input_file_path, 'r') as input_file:

        input_file.readline()

        reader = csv.reader(input_file)

        for row in reader:

            file_name = Path(row[1])
            file = file_utils.parse_recording_file_name(file_name)

            # Check that file path parsed.
            if file is None:
                continue

            night_date = get_night_date(file.start_time, STATION_TIME_ZONE)

            # Check if night date precedes start date.
            if start_date is not None and night_date < start_date:
                continue

            # Check if night date follows end date.
            if end_date is not None and night_date > end_date:
                continue

            file.channel_count = int(row[2])
            file.sample_rate = int(row[3])
            file.frame_count = int(row[4])

            files.append(file)

    return files


def get_night_date(dt, time_zone):

    start_time = dt.astimezone(time_zone)

    night_date = start_time.date()
    if start_time.hour < 12:
        night_date -= ONE_DAY

    return night_date


def create_recording_metadata_files(files, output_dir_path):
    for file in files:
        create_recording_metadata_file(file, output_dir_path)


def create_recording_metadata_file(file, output_dir_path):

    # Create output directory if needed.
    try:
        output_dir_path.mkdir(mode=0o755, parents=True, exist_ok=True)
    except Exception as e:
        logger.critical(
            f'Could not create output directory "{output_dir_path}". '
            f'Error message was: {e}')
        sys.exit(1)

    # Get file path.
    start_time = file.start_time.strftime("%Y-%m-%d_%H.%M.%S_Z")
    file_name = f'{file.station_name}_{start_time}.json'
    file_path = output_dir_path / file_name

    # Get file contents.
    station_num = STATION_NUMS.get(file.station_name)
    recorder_name = RECORDER_NAME_FORMAT.format(station_num)
    mic_output_name = MIC_OUTPUT_NAME_FORMAT.format(station_num)
    start_time = file.start_time.strftime('%Y-%m-%d %H:%M:%S Z')
    file_contents = (
        f'{{\n'
        f'    "recordings": [\n'
        f'        {{\n'
        f'            "station": "{file.station_name}",\n'
        f'            "recorder": "{recorder_name}",\n'
        f'            "mic_outputs": [\n'
        f'                "{mic_output_name}"\n'
        f'            ],\n'
        f'            "start_time": "{start_time}",\n'
        f'            "length": {file.frame_count},\n'
        f'            "sample_rate": {file.sample_rate}\n'
        f'        }}\n'
        f'    ]\n'
        f'}}\n'
    )

    # Write file.
    try:
        with open(file_path, 'w') as f:
            f.write(file_contents)
    except Exception as e:
        logger.critical(
            f'Could not write metadata file "{file_path}". '
            f'Error message was: {e}')
        sys.exit(1)


if __name__ == '__main__':
    main()
