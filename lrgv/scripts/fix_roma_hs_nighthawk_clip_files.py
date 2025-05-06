# Script that fixes the Roma HS station name in Nighthawk clip audio
# metadata files for LRGV 2025.
#
# For the first part of the 2025 spring recording season the Vesper
# Recorder was mistakenly configured with the station name "Roma"
# instead of "Roma HS". This caused audio and metadata files to be
# created with the wrong station name. This script edits the files
# to correct the station name.


from pathlib import Path
import json
import sys


'''
Here's an example of the contents of a metadata file that needs fixing:

{
    "recordings": {
        "Roma 2025-05-05 01:40:07 Z": {
            "sensors": "Roma",
            "start_time": "2025-05-05 01:40:07 Z",
            "length": 694663200,
            "sample_rate": 22050
        }
    },
    "recording_sensors": {
        "Roma": [
            "Roma 21c"
        ]
    },
    "clips": [
        {
            "recording": "Roma 2025-05-05 01:40:07 Z",
            "sensor": "Roma 21c",
            "detector": "Nighthawk 0.3.1 80",
            "start_time": "2025-05-05 02:25:48.200 Z",
            "serial_num": 0,
            "length": 39690,
            "annotations": {
                "Detector Score": "99.6819257736206",
                "Classification": "Call.DICK",
                "Classifier Score": "99.6819257736206",
                "Nighthawk Order": "Passeriformes",
                "Nighthawk Order Probability": "0.9704634",
                "Nighthawk Family": "Cardinalidae",
                "Nighthawk Family Probability": "0.9939774",
                "Nighthawk Group": "",
                "Nighthawk Group Probability": "",
                "Nighthawk Species": "DICK",
                "Nighthawk Species Probability": "0.99681926",
                "Nighthawk Predicted Category": "DICK",
                "Nighthawk Probability": "0.996819257736206",
                "Nighthawk Output File Line": "2741.2000000000003,2743.0,Roma_2025-05-05_01.40.07_Z.wav,C:\\Users\\WRE\\Desktop\\Vesper Audio\\Roma_2025-05-05_01.40.07_Z.wav,Passeriformes,0.9704634,Cardinalidae,0.9939774,,,dickci,0.99681926,dickci,0.996819257736206"
}
'''


WRONG_STATION_NAME = 'Roma'
RIGHT_STATION_NAME = 'Roma HS'

WRONG_FILE_NAME_PREFIX = WRONG_STATION_NAME + '_'
RIGHT_FILE_NAME_PREFIX = RIGHT_STATION_NAME + '_'

WRONG_FILE_NAME_PREFIX_LENGTH = len(WRONG_FILE_NAME_PREFIX)


def main():

    dir_path = Path(sys.argv[1])

    if not dir_path.exists():
        raise FileNotFoundError(f'Directory "{dir_path}" does not exist.')
    
    fix_audio_files(dir_path)
    fix_metadata_files(dir_path)


def fix_audio_files(dir_path):
    fix_files(dir_path, '*.wav', 'audio', fix_file_name)


def fix_files(dir_path, file_name_pattern, file_type, fix_file_func):

    file_paths = sorted(dir_path.rglob(file_name_pattern))

    print(f'Found {len(file_paths)} {file_type} files...')

    total_file_count = 0
    fixed_file_count = 0

    for file_path in file_paths:

        if file_has_wrong_name(file_path):
            fix_file_func(file_path)
            fixed_file_count += 1

        total_file_count += 1

        if total_file_count % 1000 == 0:
            print(f'Processed {total_file_count} files...')

    print(f'Fixed {fixed_file_count} of {total_file_count} {file_type} files.')


def file_has_wrong_name(file_path):
    return file_path.name.startswith(WRONG_FILE_NAME_PREFIX)


def fix_file_name(file_path):
    name_suffix = file_path.name[WRONG_FILE_NAME_PREFIX_LENGTH:]
    new_file_name = RIGHT_FILE_NAME_PREFIX + name_suffix
    new_file_path = file_path.parent / new_file_name
    file_path.rename(new_file_path)


def fix_metadata_files(dir_path):
    fix_files(dir_path, '*.json', 'metadata', fix_metadata_file)


def fix_metadata_file(file_path):
    fix_metadata_file_contents(file_path)
    fix_file_name(file_path)


def fix_metadata_file_contents(file_path):

    # It was tempting to just replace "Roma" with "Roma HS" globally in
    # the the metadata file contents, but that seemed a little risky
    # since I don't know for sure that all occurrences of it should
    # always be replaced. For example, I'm not certain that the
    # Nighthawk output file line will never contain, say, a taxonomic
    # name that starts with "Roma". So this function is more targeted
    # in its replacements.
 
    # Load file contents.
    with open(file_path, 'r') as file:
        metadata = json.load(file)

    # Fix recording.
    recordings = metadata['recordings']
    recording_name, recording_data = next(iter(recordings.items()))
    new_recording_name = fix_string(recording_name)
    sensors_name = recording_data['sensors']
    new_sensors_name = fix_string(sensors_name)
    recording_data['sensors'] = new_sensors_name
    recordings[new_recording_name] = recording_data
    del recordings[recording_name]
    
    # Fix recording sensors.
    sensors = metadata['recording_sensors']
    sensor_name = sensors[sensors_name][0]
    new_sensor_name = fix_string(sensor_name)
    sensors[new_sensors_name] = [new_sensor_name]
    del sensors[sensors_name]

    # Fix clips.
    clips = metadata['clips']
    for clip in clips:
        clip['recording'] = new_recording_name
        clip['sensor'] = new_sensor_name
        nighthawk_output = clip['annotations']['Nighthawk Output File Line']
        parts = nighthawk_output.split(',')
        parts[2] = fix_string(parts[2])
        parts[3] = fix_string(parts[3])
        clip['annotations']['Nighthawk Output File Line'] = ','.join(parts)

    # Dump new file contents.
    with open(file_path, 'w') as file:
        json.dump(metadata, file, indent=4)


def fix_string(s):
    return s.replace(WRONG_STATION_NAME, RIGHT_STATION_NAME)


if __name__ == '__main__':
    main()
