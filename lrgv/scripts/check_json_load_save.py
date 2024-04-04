from pathlib import Path
import json
import pprint


INPUT_FILE_PATH = Path(
    '/Users/harold/Desktop/NFC/LRGV/2024/Archiver Test Clip Folders/'
    'Alamo/Clips/Nighthawk/Incoming/Alamo_2024-09-05_02.12.11.800_Z_00.json')

OUTPUT_DIR_PATH = Path('/Users/harold/Desktop')


def main():

    with open(INPUT_FILE_PATH) as input_file:
        obj = json.load(input_file)
    pprint.pp(obj)

    obj['clips'][0]['id'] = 17

    output_file_path = OUTPUT_DIR_PATH / INPUT_FILE_PATH.name
    with open(output_file_path, 'w') as output_file:
        json.dump(obj, output_file)
        
    with open(output_file_path) as input_file:
        obj = json.load(input_file)
    pprint.pp(obj)



if __name__ == '__main__':
    main()
