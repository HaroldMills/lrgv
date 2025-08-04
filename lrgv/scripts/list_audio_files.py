"""
Script that lists information about the audio files in a directory.

Usage:

    python list_audio_files.py <directory path> <output CSV file path>

The script searches the specified directory recursively for WAVE audio
files. It writes one row of information to the specified output CSV file
for each audio file that it finds. The CSV file also includes a header row.
An example of the first two lines of such a CSV file is:

    File Path,File Name,Channel Count,Sample Rate (Hz),Frame Count,Duration
    "/Volumes/Recordings/Alamo_2025-04-09_01.22.52_Z.wav","Alamo_2025-04-09_01.22.52_Z.wav",1,22050,783127800,9:51:56.000

The script creates output file ancestor directories as needed.
"""


from pathlib import Path
import math
import sys
import wave


# TODO: Add support for other audio file formats, such as FLAC.


def main():

    dir_path, output_csv_file_path = parse_args()

    infos = get_audio_file_infos(dir_path)
    write_output_csv_file(output_csv_file_path, infos)
    
    
def parse_args():

    arg_count = len(sys.argv)

    if arg_count != 2 and arg_count != 3:
        print(
            'Usage: python list_audio_files.py '
            '<directory path> [<output CSV file path>]')
        sys.exit(1)

    dir_path = Path(sys.argv[1])

    if arg_count == 3:
        output_csv_file_path = Path(sys.argv[2])
    else:
        output_csv_file_path = None

    if not dir_path.is_dir():
        print(f'Error: Specified directory "{dir_path}" does not exist.')
        sys.exit(1)

    return dir_path, output_csv_file_path


def get_audio_file_infos(dir_path):

    infos = []

    for file_path in dir_path.glob('**/*.wav'):

        if file_path.name.startswith('.'):
            print(f'Ignoring hidden audio file "{file_path}".')
            continue

        try:
            channel_count, sample_rate, frame_count = \
                get_wave_file_info(file_path)
            
        except Exception as e:
            class_name = e.__class__.__name__
            print(
                f'Could not get info for audio file "{file_path}". '
                f'Attempt raised {class_name} exception with message: '
                f'{str(e)}. File will be ignored.')
            continue
            
        duration = frame_count / sample_rate
        
        info = (file_path, channel_count, sample_rate, frame_count, duration)
        
        infos.append(info)
    
    infos.sort()
    
    return infos


def get_wave_file_info(file_path):
    
    with wave.open(str(file_path), 'rb') as file_:
        channel_count = file_.getnchannels()
        sample_rate = file_.getframerate()
        frame_count = file_.getnframes()
    
    return channel_count, sample_rate, frame_count


def write_output_csv_file(file_path, infos):

    if file_path is None:
        write_output_csv_file_aux(sys.stdout, infos)

    else:

        # Create output file ancestor directories as needed.
        file_path.parent.mkdir(mode=0o755, parents=True, exist_ok=True)

        with open(file_path, 'w') as file:
            write_output_csv_file_aux(file, infos)


def write_output_csv_file_aux(file, infos):

    file.write(
        'File Path,File Name,Channel Count,Sample Rate (Hz),Frame Count,'
        'Duration\n')

    for file_path, channel_count, sample_rate, frame_count, duration \
            in infos:
        
        # Get file duration in the form H:MM:SS.S.
        hours = int(duration // 3600)
        minutes = int((duration // 60) % 60)
        seconds = int(math.floor(duration % 60))
        millis = int(round(1000 * (duration % 1)))
        duration = f'{hours}:{minutes:02d}:{seconds:02d}.{millis:03d}'

        file.write(
            f'"{file_path}","{file_path.name}",{channel_count},'
            f'{sample_rate},{frame_count},{duration}\n')
           
    
if __name__ == '__main__':
    main()
