# Script that trims Nighthawk output file line annotations as needed in
# 2025 LRGV and Lighthouse clip metadata files. As created by the
# Nighthawk runner, some of the annotations have more than 255 characters,
# which is the maximum string annotation value length allowed in a Vesper
# archive database.
#
# The script only modifies annotation values that are too long. It
# shortens them by replacing the recording file path of the annotation
# value (i.e. the 4th column) with the empty string. The recording file
# name (i.e. the last component of the file path) remains in the 3rd
# column of the annotation value.


from pathlib import Path
import json
import sys


def main():

    dir_path = Path(sys.argv[1])

    if not dir_path.exists():
        raise FileNotFoundError(f'Directory "{dir_path}" does not exist.')
    
    file_paths = sorted(dir_path.rglob('*.json'))

    print(f'Found {len(file_paths)} JSON files...')

    total_file_count = 0
    modified_file_count = 0

    for file_path in file_paths:

        with open(file_path, 'r') as file:
            metadata = json.load(file)

        # Get Nighthawk output file line annotation value.
        annotations = metadata['clips'][0]['annotations']
        line = annotations['Nighthawk Output File Line']

        if len(line) > 255:

            # Remove file path from annotation value.
            parts = line.split(',')
            parts[3] = ''
            new_line = ','.join(parts)
            annotations['Nighthawk Output File Line'] = new_line

            with open(file_path, 'w') as file:
                json.dump(metadata, file, indent=4)

            print(f'file path "{file_path}" {len(line)} -> {len(new_line)}')
            print(f'{line}')
            print(f'{new_line}')
            print()

            modified_file_count += 1

        total_file_count += 1

        if total_file_count % 1000 == 0:
            print(f'Processed {total_file_count} files...')

    print(f'Modified {modified_file_count} of {total_file_count} JSON files.')


if __name__ == '__main__':
    main()
