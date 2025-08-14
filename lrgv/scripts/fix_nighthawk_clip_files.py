# Script that fixes a problem with Nighthawk clip files created by
# the LRGV Nighthawk runner prior to the night of 2025-04-15.
#
# Prior to the night of 2025-04-15, the LRGV 2025 Nighthawk runner
# put incorrect recording and clip start times in the names of the
# metadata and audio files it created, as well as in the contents
# of the metadata files. The start times were five for some early
# Alamo files) or four hours (for later Alamo files and files from
# all other stations) after they should have been. This script fixes
# the contents of the metadata files and renames the metadata and
# audio files to have the correct start times.
#
# The script operates nonrecursively on the files of a single directory.


from pathlib import Path
import json
import sys


STATION_NUMS = {
    'Alamo': 0,
    'Donna': 1,
    'Harlingen': 2,
    'Port Isabel': 3,
    'Rio Hondo': 4,
    'Roma HS': 5,
    'Roma RBMS': 6,
    'Rio Grande City': 7
}

RECORDER_NAME_FORMAT = 'Vesper Recorder {}'
MIC_OUTPUT_NAME_FORMAT = '21c {} Vesper Output'


def main():

    dir_path = Path(sys.argv[1])

    if not dir_path.exists():
        raise FileNotFoundError(f'Directory "{dir_path}" does not exist.')
    
    metadata_file_paths = sorted(dir_path.glob('*.json'))

    print(
        f'Updating {len(metadata_file_paths)} clip file pairs in '
        f'directory "{dir_path}"...')

    for file_path in metadata_file_paths:
        clip_start_time = update_metadata_file(file_path)
        update_file_names(file_path, clip_start_time)

    print('Done.')


def update_metadata_file(file_path):
        
    with open(file_path, 'r') as file:

        metadata = json.load(file)

        # Get start time offset from metadata.
        start_time_offset = get_start_time_offset(metadata)

        # Fix recording start time.
        recording = get_recording(metadata)
        recording['start_time'] = \
            fix_start_time(recording['start_time'], start_time_offset)

        # Fix clip start time.
        clip = get_clip(metadata)
        clip_start_time = \
            fix_start_time(clip['start_time'], start_time_offset)
        clip['start_time'] = clip_start_time

    # print(f'"{file_path}" {start_time_offset}:')
    # print(json.dumps(metadata, indent=4))

    with open(file_path, 'w') as file:
        json.dump(metadata, file, indent=4)

    return clip_start_time


def get_start_time_offset(d):

    # Note that in this function we assume that the only incorrect
    # field in our start times is the hour, i.e. that the correction
    # doesn't cross a UTC midnight.

    # Get bad start time hour from recording metadata.
    recording = get_recording(d)
    bad_recording_start_time = recording['start_time']
    bad_hour = int(bad_recording_start_time.split(' ')[1][:2])

    # Get good start time hour from Nighthawk Output File Line.
    clip = get_clip(d)
    line = clip['annotations']['Nighthawk Output File Line']
    recording_file_name = line.split(',')[2]
    good_hour = int(recording_file_name.split('_')[2][:2])

    return good_hour - bad_hour


def get_recording(d):
    return next(iter(d['recordings'].values()))


def fix_start_time(start_time, start_time_offset):
    parts = start_time.split(' ')
    hour = int(parts[1][:2])
    new_hour = hour + start_time_offset
    if new_hour < 0:
        raise ValueError(
            'Hour correction crossed a midnight boundary. '
            'That is not currently supported by this script.')
    parts[1] = f'{new_hour:02d}' + parts[1][2:]
    return ' '.join(parts)


def get_clip(d):
    return d['clips'][0]


def update_file_names(metadata_file_path, start_time):

    # Get file name version of clip start time, e.g. 2025-04-15_01.23.45.678_Z.
    start_time = start_time.replace(':', '.')
    start_time = start_time.replace(' ', '_')

    rename_file(metadata_file_path, start_time)

    audio_file_path = metadata_file_path.with_suffix('.wav')
    rename_file(audio_file_path, start_time)


def rename_file(file_path, start_time):
    parts = file_path.name.split('_')
    new_file_name = '_'.join((parts[0], start_time, parts[-1]))
    new_file_path = file_path.with_name(new_file_name)
    # print(f'Rename "{file_path}" -> "{new_file_path}"')
    file_path.rename(new_file_path)


if __name__ == '__main__':
    main()
