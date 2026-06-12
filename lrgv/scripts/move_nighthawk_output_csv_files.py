# Script that moves Nighthawk output .csv files from the Synced Station Data
# directory hierarchy to the Nighthawk Output Files directory hierarchy for
# each of a list of stations.
#
# This script should be run before backing up (i.e. copying to one of the
# NFC Data disks) the Nighthawk Output Files directory.


import argparse
from pathlib import Path


PROJECT_STATIONS = {
    'Lighthouse': (
        'BBBO',
        'Barker',
        'Golden Hill',
        'Hamlin Beach',
        'Hilton',
        'Kendall',
        'Lakeside',
        'Lyndonville',
        'Newfane',
        'Station 1',
        'Station 5',
        'Wilson',
    ),
    'LRGV': ('Alamo', 'Donna', 'Harlingen', 'Rio Grande City', 'Roma RBMS')
}

SUBDIR_PATH = Path('Clips/Nighthawk/Nighthawk Output')


def main():
    
    parser = argparse.ArgumentParser(
        description='Move Nighthawk output CSV files.')
    parser.add_argument(
        'project_name', help='Name of the project (e.g., Lighthouse)')
    args = parser.parse_args()
    
    project_name = args.project_name
    
    if project_name not in PROJECT_STATIONS:
        print(f'Unrecognized project name "{project_name}".')
        return
        
    station_names = PROJECT_STATIONS[project_name]
    
    base_dir_path = Path(
        f'/Users/harold/Desktop/NFC/Data/Old Bird/{project_name}/2026')
    
    for station_name in station_names:

        source_dir_path = (
            base_dir_path /
            'Synced Station Data' /
            f'{project_name} - {station_name}' /
            SUBDIR_PATH)

        dest_dir_path = (
            base_dir_path /
            'Nighthawk Output Files' /
            station_name)

        move_csv_files(station_name, source_dir_path, dest_dir_path)


def move_csv_files(station_name, source_dir_path, dest_dir_path):

    if not source_dir_path.exists():
        print(
            f'Station "{station_name}": source directory does not exist: '
            f'"{source_dir_path}"')
        return

    csv_files = sorted(source_dir_path.glob('*.csv'))

    if len(csv_files) == 0:
        print(f'Station "{station_name}": no .csv files found.')
        return

    dest_dir_path.mkdir(parents=True, exist_ok=True)

    for file_path in csv_files:
        dest_file_path = dest_dir_path / file_path.name
        file_path.rename(dest_file_path)
        print(f'Moved "{file_path.name}" to "{dest_dir_path}".')

    print(f'Station "{station_name}": moved {len(csv_files)} .csv file(s).')


if __name__ == '__main__':
    main()
