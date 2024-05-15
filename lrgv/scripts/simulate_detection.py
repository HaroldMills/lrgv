from pathlib import Path
import itertools
import shutil
import time


# The source, active, and retired test data directory hierarchies parallel
# the laptop data directory hierarchy and look like:
#
#     <root dir>
#         <station name>
#             Clips
#                 <detector name>
#                     Incoming
#                     Created
#                     Archived
#
# For a given station, Old Bird detector clips appear in the station
# directory <station name>, while other detector clips appear in the
# `Incoming` directory.


DATA_SOURCE_DIR_PATH = \
    Path('/Users/harold/Desktop/NFC/LRGV/2024/Archiver Test Data Source')

DATA_DIR_PATH = Path('/Users/harold/Desktop/NFC/LRGV/2024/Archiver Test Data')

ACTIVE_DATA_DIR_PATH = DATA_DIR_PATH / 'Active'

RETIRED_DATA_DIR_PATH = DATA_DIR_PATH / 'Retired'

DATA_DIR_PATHS = (ACTIVE_DATA_DIR_PATH, RETIRED_DATA_DIR_PATH)

CLIP_DIR_NAME = 'Clips'

INCOMING_DIR_NAME = 'Incoming'

DETECTOR_CLIP_DIR_NAMES = (INCOMING_DIR_NAME, 'Created', 'Archived')

STATION_NAMES = ('Alamo', 'Rio Hondo')

DETECTOR_NAMES = ('Dick', 'Nighthawk')

DETECTION_SLEEP_PERIOD = 2

MAX_CLIP_COUNT = None


chain = itertools.chain.from_iterable


def main():

    print(f'Clearing test data directories...')
    clear_dirs()

    clip_count = 0

    for audio_file_path in get_clip_audio_file_paths():

        if MAX_CLIP_COUNT is not None and clip_count == MAX_CLIP_COUNT:
            break

        relative_path = audio_file_path.relative_to(DATA_SOURCE_DIR_PATH)
        print(f'Detected "{relative_path}...')

        detect_clip(audio_file_path)

        clip_count += 1

        time.sleep(DETECTION_SLEEP_PERIOD)
        

def clear_dirs():

    def clear_dir(dir_path):
        if dir_path.exists():
            for path in dir_path.glob('*'):
                if path.is_file():
                    path.unlink()
        
    for data_dir_path in DATA_DIR_PATHS:

        for station_name in STATION_NAMES:

            station_dir_path = data_dir_path / station_name
            
            clear_dir(station_dir_path)

            clip_dir_path = station_dir_path / CLIP_DIR_NAME
            
            for detector_name in DETECTOR_NAMES:

                detector_dir_path = clip_dir_path / detector_name

                for dir_name in DETECTOR_CLIP_DIR_NAMES:
                    dir_path = detector_dir_path / dir_name
                    clear_dir(dir_path)


def get_clip_audio_file_paths():
    old_bird_paths = get_old_bird_clip_audio_file_paths()
    other_paths = get_other_clip_audio_file_paths()
    path_lists = old_bird_paths + other_paths
    zipped_paths = list(itertools.zip_longest(*path_lists))
    return [p for p in chain(zipped_paths) if p is not None]


def get_old_bird_clip_audio_file_paths():

    def get_clips_aux(station_name):
        dir_path = DATA_SOURCE_DIR_PATH / station_name
        return sorted(p for p in dir_path.glob('*.wav'))
    
    return [get_clips_aux(n) for n in STATION_NAMES]


def get_other_clip_audio_file_paths():

    def get_clips_aux(station_name, detector_name):
        dir_path = \
            DATA_SOURCE_DIR_PATH / station_name / CLIP_DIR_NAME / \
            detector_name / INCOMING_DIR_NAME
        return sorted(p for p in dir_path.glob('*.wav'))

    cases = itertools.product(STATION_NAMES, DETECTOR_NAMES)
    return [get_clips_aux(s, d) for s, d in cases]


def detect_clip(audio_file_path):

    relative_path = audio_file_path.relative_to(DATA_SOURCE_DIR_PATH)
    to_dir_path = ACTIVE_DATA_DIR_PATH / relative_path.parent

    shutil.copy2(audio_file_path, to_dir_path)

    metadata_file_path = audio_file_path.with_suffix('.json')
    if metadata_file_path.exists():
        shutil.copy2(metadata_file_path, to_dir_path)


if __name__ == '__main__':
    main()
