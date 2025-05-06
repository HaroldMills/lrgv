# Script that updates Nighthawk clip metadata files for 2025 LRGV and
# Lighthouse archiving.
#
# The updates change the terms in which devices are described from
# sensors to recorders and mic outputs. The new format also supports
# multichannel recordings and metadata files that contain only
# recordings or only clips.


from pathlib import Path
import json
import sys


STATION_NUMS = {
    'Alamo': 0,
    'Donna': 1,
    'Harlingen': 2,
    'Port Isabel': 3,
    'Rio Hondo': 4,
    'Roma HS': 5,
    'Roma RBMS': 6
}

RECORDER_NAME_FORMAT = 'Vesper Recorder {}'
MIC_OUTPUT_NAME_FORMAT = '21c {} Vesper Output'


def main():

    dir_path = Path(sys.argv[1])

    if not dir_path.exists():
        raise FileNotFoundError(f'Directory "{dir_path}" does not exist.')
    
    file_paths = sorted(dir_path.rglob('*.json'))

    print(f'Found {len(file_paths)} JSON files...')

    total_file_count = 0
    updated_file_count = 0

    for file_path in file_paths:

        with open(file_path, 'r') as file:
            metadata = json.load(file)

        if 'recording_sensors' in metadata:
            # file is not already updated

            metadata = update_metadata(metadata)

            with open(file_path, 'w') as file:
                json.dump(metadata, file, indent=4)

            updated_file_count += 1

        total_file_count += 1

        if total_file_count % 1000 == 0:
            print(f'Processed {total_file_count} files...')

    print(f'Updated {updated_file_count} of {total_file_count} JSON files.')


def update_metadata(d):

    recording = get_recording(d)
    station_name = recording['sensors']
    station_num = STATION_NUMS[station_name]
    recorder_name = RECORDER_NAME_FORMAT.format(station_num)
    mic_output_name = MIC_OUTPUT_NAME_FORMAT.format(station_num)

    recordings = [
        {
            'station': station_name,
            'recorder': recorder_name,
            'mic_outputs': [mic_output_name],
            'start_time': recording['start_time'],
            'length': recording['length'],
            'sample_rate': recording['sample_rate'],
        }
    ]

    clips = [
        get_clip(c, station_name, mic_output_name)
        for c in d['clips']]

    return {
        'recordings': recordings,
        'clips': clips
    }


def get_recording(d):
    return next(iter(d['recordings'].values()))


def get_clip(c, station_name, mic_output_name):

    return {
        'station': station_name,
        'mic_output': mic_output_name,
        'detector': c['detector'],
        'start_time': c['start_time'],
        'serial_num': c['serial_num'],
        'length': c['length'],
        'annotations': c['annotations'],
    }


if __name__ == '__main__':
    main()
