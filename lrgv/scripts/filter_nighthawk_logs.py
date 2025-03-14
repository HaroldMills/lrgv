# Script that filters LRGV Nighthawk logs.
#
# The script removes two kinds of lines that are not useful and bloat
# the logs.
#
# Run the script from the directory whose log files you want to filter.
# The script searches the directory hierarchy rooted at the current
# working directory for files named "run_nighthawk.log" and filters
# them, writing the filtered logs to an output directory named
# "LRGV Nighthawk Logs" on the Desktop. The script creates output
# directories as needed.


from pathlib import Path


FILTER_STRING_1 = (
    'run_reconstructed_model.py:586: FutureWarning: Series.__getitem__ '
    'treating keys as positions is deprecated. In a future version, '
    'integer keys will always be treated as labels (consistent with '
    'DataFrame behavior). To access a value by position, use `ser.iloc[pos]`')

FILTER_STRING_2 = 'return(x[0])'

OUTPUT_DIR_PATH = Path('/Users/harold/Desktop/LRGV Nighthawk Logs')

OUTPUT_FILE_NAME = Path('run_nighthawk_2.log')


def process_file(input_file_path, output_file_path):

    # Create output file parent directory if needed.
    output_file_path.parent.mkdir(parents=True, exist_ok=True)

    with input_file_path.open('rb') as input_file, \
            output_file_path.open('wb') as output_file:
        
        for line in input_file:

            decoded_line = line.decode('utf-8')

            if FILTER_STRING_1 not in decoded_line and \
                    FILTER_STRING_2 not in decoded_line:
                
                output_file.write(line)


def main():
    dir_path = Path.cwd()
    for path in dir_path.rglob('run_nighthawk.log'):
        station_name = path.parent.parent.parent.name
        output_file_path = OUTPUT_DIR_PATH / station_name / OUTPUT_FILE_NAME
        print(f'Processing file "{path.relative_to(dir_path)}"...')
        process_file(path, output_file_path)


if __name__ == "__main__":
    main()