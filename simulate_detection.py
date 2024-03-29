from pathlib import Path
import itertools
import shutil
import time


# The test clip directory hierarchy looks like:
#
#     <test data directory>
#         <station name>
#             <detector name>
TEST_CLIP_DIR_PATH = \
    Path('/Users/harold/Desktop/NFC/LRGV/2024/Archiver Test Clips')

# The clip folder directory hierarchy parallels the station laptop
# clip folder hierarchy and looks like:
#
#     <clip folder>
#         <station name>
#             Clips
#                 <detector name>
#                     Incoming
CLIP_FOLDER_DIR_PATH = \
    Path('/Users/harold/Desktop/NFC/LRGV/2024/Archiver Test Clip Folders')

STATION_CLIP_DIR_NAME = 'Clips'

INCOMING_DIR_NAME = 'Incoming'

DETECTOR_CLIP_DIR_NAMES = (INCOMING_DIR_NAME,)

STATION_NAMES = ['Alamo', 'Rio Hondo']

DETECTOR_NAMES = ['Nighthawk']

CLEARING_SLEEP_PERIOD = 5
DETECTION_SLEEP_PERIOD = .5

MAX_CLIP_COUNT = None


chain = itertools.chain.from_iterable
product = itertools.product


def main():

    print(f'Clearing clip folders...')
    clear_dirs()

    time.sleep(CLEARING_SLEEP_PERIOD)

    clip_count = 0

    for audio_file_path in get_clip_audio_file_paths():

        if MAX_CLIP_COUNT is not None and clip_count == MAX_CLIP_COUNT:
            break

        print(f'Detected "{audio_file_path.name}...')

        detect_clip(audio_file_path)

        clip_count += 1

        time.sleep(DETECTION_SLEEP_PERIOD)
        

def clear_dirs():

    def clear_dir(dir_path):
        for file_path in dir_path.glob('*'):
            file_path.unlink()
        
    for station_name in STATION_NAMES:

        station_dir_path = \
            CLIP_FOLDER_DIR_PATH / station_name / STATION_CLIP_DIR_NAME
        
        for detector_name in DETECTOR_NAMES:

            detector_dir_path = station_dir_path / detector_name

            for dir_name in DETECTOR_CLIP_DIR_NAMES:
                dir_path = detector_dir_path / dir_name
                clear_dir(dir_path)


def get_clip_audio_file_paths():

    def get_clips_aux(station_name, detector_name):
        dir_path = TEST_CLIP_DIR_PATH / station_name / detector_name
        return sorted(p for p in dir_path.glob('*.wav'))

    cases = product(STATION_NAMES, DETECTOR_NAMES)
    clip_tuples = zip(*(get_clips_aux(s, d) for s, d in cases))
    return chain(clip_tuples)


def detect_clip(audio_file_path):

    station_name = audio_file_path.parent.parent.name
    detector_name = audio_file_path.parent.name

    to_dir_path = \
        CLIP_FOLDER_DIR_PATH / station_name / STATION_CLIP_DIR_NAME / \
            detector_name / INCOMING_DIR_NAME
    
    shutil.copy(audio_file_path, to_dir_path)

    metadata_file_path = audio_file_path.with_suffix('.json')
    shutil.copy(metadata_file_path, to_dir_path)


if __name__ == '__main__':
    main()
