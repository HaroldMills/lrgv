"""
Script that lists LRGV 2025 Dick-r clips that are missing both from
the cloud archive and from a local directory.
"""


from collections import defaultdict
from datetime import datetime as Datetime, timedelta as TimeDelta
from pathlib import Path
from zoneinfo import ZoneInfo


ALL_CLIP_LIST_FILE_PATH = Path('/Users/harold/Desktop/Old Bird/files.txt')

MISSING_CLIP_LIST_FILE_PATH = Path(
    '/Users/harold/Desktop/Old Bird/Clips missing from LRGV cloud archive.txt')

CLIP_ROOT_DIR_PATH = Path(
    '/Users/harold/Desktop/NFC/Data/Old Bird/LRGV/2025/Missing Clips')

CENTRAL_TIME_ZONE = ZoneInfo('US/Central')

CLASSIFICATIONS = {
    'calls': 'Call.DICK',
    'noise': 'Noise'
}

CLASSIFICATION_DIR_NAMES = {
    'Call.DICK': 'calls',
    'Noise': 'noise'
}


def main():

    all_clip_file_paths = get_all_clip_file_paths()
    missing_clip_info = get_missing_clip_info()
    available_clip_file_paths = get_available_clip_file_paths()

    clip_count = 0
    unavailable_clip_count = 0

    for station_name, file_name, classification in missing_clip_info:

        file_path = find_missing_file(
            station_name, file_name, available_clip_file_paths)

        if file_path is None:

            file_paths = all_clip_file_paths.get((station_name, file_name))

            if file_paths is None:
                print(f'No clip file found for "{station_name}" {file_name}.')

            else:
                print(
                    f'No clip file found for "{station_name}" {file_name}. '
                    f'Listed paths were {file_paths}.')
                unavailable_clip_count += 1

        clip_count += 1

    print(
        f'Clip files are not available for {unavailable_clip_count} of '
        f'{clip_count} clips.')


def get_all_clip_file_paths():

    paths = defaultdict(set)

    with open(ALL_CLIP_LIST_FILE_PATH, 'r') as file:
        lines = file.readlines()

    for line in lines:

        file_path = line.strip()
        parts = file_path[3:].split('\\')

        if len(parts) == 7:
            station_name = parts[4]
            file_name = parts[-1]
            paths[(station_name, file_name)].add(file_path)

    return paths


def get_missing_clip_info():

    with open(MISSING_CLIP_LIST_FILE_PATH, 'r') as file:
        lines = file.readlines()

    return sorted(parse_missing_clip_line(l) for l in lines)


def parse_missing_clip_line(line):
    station_name, start_time, classification = line.strip().split('_')
    file_name = get_clip_file_name(start_time)
    return (station_name, file_name, classification)


def parse_file_line(line):
    station_name, start_time, classification = line.strip().split('_')
    file_name = get_clip_file_name(start_time)
    return station_name, file_name, classification


def get_clip_file_name(start_time):

    # Get clip start time in station time zone.
    dt = Datetime.fromisoformat(start_time)
    dt = dt.astimezone(CENTRAL_TIME_ZONE)

    # Extract clip number from start time.
    num = dt.microsecond

    # Format start time.
    start_time = dt.strftime('%Y-%m-%d_%H.%M.%S')

    return f'Dick_{start_time}_{num:02d}.wav'


def get_available_clip_file_paths():
        
    info = {}

    for abs_file_path in CLIP_ROOT_DIR_PATH.rglob('*.wav'):
        rel_file_path = abs_file_path.relative_to(CLIP_ROOT_DIR_PATH)
        station_name = rel_file_path.parts[0]
        file_name = rel_file_path.name
        info[(station_name, file_name)] = abs_file_path

    return info


def find_missing_file(station_name, file_name, available_clip_file_paths):

    file_path = available_clip_file_paths.get((station_name, file_name))

    if file_path is None and station_name == 'Port Isabel' and \
            get_night(file_name) == '2025-04-26':
        
        file_path = available_clip_file_paths.get(('Harlingen', file_name))

    return file_path


def get_night(file_name):

    parts = file_name.split('_')
    date = parts[1]
    time = parts[2].replace('.', ':')

    dt = date + 'T' + time
    dt = Datetime.fromisoformat(dt)

    night = dt.date()
    if dt.hour < 12:
        night -= TimeDelta(days=1)

    return str(night)


if __name__ == '__main__':
    main()
