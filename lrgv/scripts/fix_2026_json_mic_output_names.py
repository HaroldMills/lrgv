"""
Script that replaces "Vesper Output" with "Output" in all .json files
within the LRGV 2026 active station data directory.

I wrote this script with the help of Gemini 3.1 Pro to fix some bad
microphone output names in LRGV recording and clip JSON files at the
beginning of the 2026 season.
"""


from pathlib import Path


DIR_PATH = Path(
    '/Users/harold/Desktop/NFC/Data/Old Bird/LRGV/2026/Station Data/Active')


def main():

    if not DIR_PATH.is_dir():
        print(f'Error: {DIR_PATH} is not a valid directory.')
        return

    # Find all .json files in the specified directory and its subdirectories.
    json_files = list(DIR_PATH.rglob('*.json'))
    
    if len(json_files) == 0:
        print(f'No .json files found in {DIR_PATH} or its subdirectories')
        return

    for file_path in json_files:

        try:
            content = file_path.read_text(encoding='utf-8')
            
            # Check if the string exists to avoid unnecessary writes.
            if 'Vesper Output' in content:
                new_content = content.replace('Vesper Output', 'Output')
                file_path.write_text(new_content, encoding='utf-8')
                print(f'Modified: {file_path}')
            else:
                print(f'No changes needed: {file_path}')
                
        except Exception as e:
            print(f'Error processing {file_path}: {e}')


if __name__ == '__main__':
    main()
