from datetime import date as Date
from pathlib import Path
import logging

from lrgv.archiver.app_settings import app_settings
from lrgv.archiver.old_bird_clip_converter import OldBirdClipConverter
from lrgv.dataflow import Graph
from lrgv.util.bunch import Bunch


logger = logging.getLogger(__name__)


class ClassifiedOldBirdClipArchiver(Graph):


    def _create_processors(self):

        classification_subdir_names = ('calls', 'noise')
        classifications = {'calls': 'Call.DICK', 'noise': 'Noise'}

        station_names = app_settings.station_names
        # station_name_set = frozenset(station_names)

        processors = []

        for night_dir_path in get_night_dir_paths():

            # check_night_subdirs(night_dir_path, station_name_set)

            for station_name in station_names:

                station_dir_path = night_dir_path / station_name

                if station_dir_path.exists():

                    for subdir_name in classification_subdir_names:

                        subdir_path = station_dir_path / subdir_name

                        if not subdir_path.exists:
                            logger.warning(
                                f'Clip directory "{subdir_path}" does not '
                                f'exist.')
                            
                        else:
                            classification = classifications[subdir_name]
                            processor = _create_old_bird_clip_converter(
                                station_name, subdir_path, classification)
                            processors.append(processor)

                            path_count = len(list(subdir_path.glob('*')))
                            logger.info(f'{path_count} {subdir_path}')

        return processors


def check_night_subdirs(night_dir_path, station_name_set):

    subdir_paths = [p for p in night_dir_path.glob('*') if p.is_dir()]

    dir_names = set()

    for p in subdir_paths:

        if p.name not in station_name_set:
            logger.warning(
                f'Final component of path "{p}" is not a station name.')
            
        else:
            dir_names.add(p.name)

    missing_dir_names = station_name_set - dir_names

    if len(missing_dir_names) != 0:
        logger.warning(
            f'Night directory {night_dir_path.name} missing subdirectories '
            f'for stations {missing_dir_names}.')

        
def get_night_dir_paths():

    root_dir_path = Path(
        '/Users/harold/Desktop/NFC/LRGV/Synced Folders 2024/DICK data')
    
    dir_paths = [
        p for p in root_dir_path.glob('*')
        if p.name.endswith('Apr') or p.name.endswith('May')]
    
    dir_paths.sort(key=lambda p: get_dir_path_date(p))
    
    # for path in dir_paths:
    #     print(path)

    return dir_paths


def get_dir_path_date(dir_path):

    dir_name = dir_path.name

    if dir_name.endswith('Apr'):
        month = 4
    else:
        month = 5

    day = int(dir_name.split('-')[0])

    if month == 5 and day == 30:
        month = 4

    return Date(2024, month, day)


def _create_old_bird_clip_converter(
        station_name, clip_dir_path, classification):
    
    name = f'Old Bird Clip Converter for {clip_dir_path}'

    s = app_settings
    station_paths = s.paths.stations[station_name]

    settings = Bunch(
        station_name=station_name,
        source_clip_dir_path=clip_dir_path,
        clip_file_wait_period=s.clip_file_wait_period,
        station_paths=station_paths,
        clip_classification=classification)
        
    return OldBirdClipConverter(name, settings)
