# Script that moves .wav and .json files from one directory hierarchy to
# another if they were last modified at least a certain time ago. The
# script creates target directories as needed.
#
# Usage: python move_clip_files.py <source_dir_path> <target_dir_path>


from pathlib import Path
import sys
import time


FILE_NAME_EXTENSIONS = ('.wav', '.json')
# FILE_AGE_THRESHOLD = 48 * 3600
FILE_AGE_THRESHOLD = 0
SOURCE_DIR_NAME = 'Active'
TARGET_DIR_NAME = 'Stashed'


def main():

    source_dir_path = Path(sys.argv[1])
    target_dir_path = Path(sys.argv[2])

    if not source_dir_path.exists():
        raise FileNotFoundError(
            f'Source directory "{source_dir_path}" does not exist.')

    time_limit = time.time() - FILE_AGE_THRESHOLD

    for file_name_extension in FILE_NAME_EXTENSIONS:
        move_files(
            source_dir_path, target_dir_path, file_name_extension, time_limit)


def move_files(
        source_dir_path, target_dir_path, file_name_extension, time_limit):

    file_count = 0

    for file_path in source_dir_path.rglob(f'*{file_name_extension}'):

        if file_path.suffix in FILE_NAME_EXTENSIONS:

            last_mod_time = file_path.stat().st_mtime

            if last_mod_time <= time_limit:

                # Get target file path.
                relative_path = file_path.relative_to(source_dir_path)
                target_file_path = target_dir_path / relative_path

                # Create target file parent directory if needed.
                target_file_path.parent.mkdir(parents=True, exist_ok=True)

                # Move file to target directory.
                # print(f'Move "{file_path}" to "{target_file_path}"...')
                file_path.rename(target_file_path)

                file_count += 1

                if file_count % 1000 == 0:
                    print(f'Moved {file_count} {file_name_extension} files...')

    print(f'Moved a total of {file_count} {file_name_extension} files.')


if __name__ == '__main__':
    main()
