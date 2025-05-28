"""
Transfers GlassOFire classifications for 2025 LRGV Dick-r clips to
Vesper archive.

Bill Evans classified many LRGV 2025 Dick-r clips manually using Old
Bird's GlassOFire program. GlassOFire moves classified clips to
directories whose names indicate the clips' classifications. This script
transfers such classifications to the LRGV 2025 Vesper cloud archive.
Its input is a text file that recursively lists all of the .wav files
in the GlassOFire classification directory hierarchy.
"""


from collections import defaultdict
from datetime import \
    date as Date, datetime as Datetime, timedelta as TimeDelta
from pathlib import Path
from zoneinfo import ZoneInfo
import re

from django.db import transaction

# Set up Django. This must happen before any use of Django, including
# ORM class imports.
import vesper.util.django_utils as django_utils
django_utils.set_up_django()

from vesper.django.app.models import (
    AnnotationInfo, Clip, Processor, Station, StringAnnotation,
    StringAnnotationEdit, User)

CLASSIFICATION_FILE_PATH = Path('/Users/harold/Desktop/Old Bird/files.txt')

CLIP_FILE_NAME_RE = re.compile(
    r'^'
    f'Dick_'
    r'(?P<year>\d\d\d\d)-(?P<month>\d\d)-(?P<day>\d\d)'
    r'_'
    r'(?P<hour>\d\d)\.(?P<minute>\d\d)\.(?P<second>\d\d)'
    r'_'
    r'(?P<num>\d\d)'
    r'\.(?:wav|WAV)'
    r'$')

STATION_NAMES = frozenset((
    'Alamo',
    'Donna',
    'Harlingen',
    'Port Isabel',
    'Rio Hondo',
    'Roma HS',
    'Roma RBMS'
))

CLASSIFICATIONS = {
    'calls': 'Call.DICK',
    'noise': 'Noise'
}

CENTRAL_TIME_ZONE = ZoneInfo('US/Central')
UTC_TIME_ZONE = ZoneInfo('UTC')


# Model Django ORM code on
# scripts/detector_eval/manual/classify_unclassified_clips.py


DETECTOR_NAME = 'Old Bird Dickcissel Detector 1.0'
CUTOFF_DATE = Date(2025, 5, 7)
USER_NAME = 'BillEvans'
ANNOTATION_NAME = 'Classification'



def main():

    # Get station name -> clip start time -> classification map from file.
    classifications = load_classifications()

    # Get station name -> clip start time -> clip map from archive database.
    clips = get_clips()

    show_archived_clips_not_in_file(clips, classifications)

    transfer_classifications(clips, classifications)


def load_classifications():

    print('Loading classifications from file...')

    with open(CLASSIFICATION_FILE_PATH, 'r') as file:

        bad_clip_file_name_count = 0
        unrecognized_station_name_count = 0
        unrecognized_classification_count = 0
        unrecognized_classifications = set()
        good_line_count = 0
        classification_sets = defaultdict(set)
        duplicate_clips = set()
        duplicate_clip_lines = defaultdict(set)
        duplicate_clip_line_count = 0

        for line in file:

            line = line.strip()

            parts = line.split('\\')

            # Parse clip file name
            file_name = parts[-1]
            m = CLIP_FILE_NAME_RE.match(file_name)
            if m is None:
                bad_clip_file_name_count += 1
                continue
            else:
                start_time = parse_start_time(file_name)            

            # Parse station name.
            station_name = parts[5]
            if station_name not in STATION_NAMES:
                unrecognized_station_name_count += 1
                continue

            # Parse classification.
            classification = parts[-2]
            try:
                classification = CLASSIFICATIONS[classification]
            except KeyError:
                unrecognized_classification_count += 1
                unrecognized_classifications.add(classification)
                classification = 'None'
                
            # If we get here, we successfully parsed the line.

            good_line_count += 1

            key = (station_name, start_time)

            if key in classification_sets:
                duplicate_clips.add(key)
                duplicate_clip_lines[key].add(line)
                duplicate_clip_line_count += 1
                
            classification_sets[key].add(classification)
 
        print(f'Successfully parsed {good_line_count} file lines.')

        print(
            f'Could not parse clip file name for {bad_clip_file_name_count} '
            f'file lines.')
        
        print(
            f'Did not recognized station names for '
            f'{unrecognized_station_name_count} file lines.')
        
        print(
            f'Did not recognize classifications for '
            f'{unrecognized_classification_count} file lines.')
        
        print(
            f'Unrecognized classifications were: '
            f'{unrecognized_classifications}')
        
        print(f'There were {duplicate_clip_line_count} duplicate clip lines.')

        non_duplicate_line_count = good_line_count - duplicate_clip_line_count
        print(
            f'There were {non_duplicate_line_count} non-duplicate clip lines.')
        
        # Show distinct duplicate classification sets.
        duplicate_clip_classification_counts = defaultdict(int)
        for key in duplicate_clips:
            classifications = tuple(sorted(classification_sets[key]))
            duplicate_clip_classification_counts[classifications] += 1
        print('Duplicate clip counts by classifications were:')
        for classifications, count in \
                duplicate_clip_classification_counts.items():
            print(f'    {classifications} {count}')

        # Get clip classifications, including for clips for which there
        # were multiple file lines.
        classifications = defaultdict(dict)
        for (station_name, start_time), classification_set in \
                classification_sets.items():
            classifications[station_name][start_time] = \
                get_classification(classification_set)
            
        print()
            
    return classifications


def get_classification(classifications):

    # Remove any 'None' classifications.
    classifications = tuple(c for c in classifications if c != 'None')

    if len(classifications) == 1:
        # there's exactly one classification left

        return classifications[0]
    
    else:
        # there are either no classifications or more than one
        # classification left

        return None


def parse_start_time(clip_file_name):

    # Example clip file name: Dick_2025-05-03_04.02.06_00.wav

    # Remove initial "Dick_" and final ".wav\n".
    s = clip_file_name[5:-5]

    date, time, num = s.split('_')

    dt = Datetime.strptime(f'{date} {time}', '%Y-%m-%d %H.%M.%S')
    num = int(num)
    dt += TimeDelta(microseconds=num)
    dt = dt.replace(tzinfo=CENTRAL_TIME_ZONE)
    dt = dt.astimezone(UTC_TIME_ZONE)

    return dt


def get_clips():

    print('Getting clips from archive database...')

    clips = defaultdict(dict)
    clip_count = 0

    stations = get_stations()
    detector = get_detector(DETECTOR_NAME)

    for station in stations:

        station_clips = get_station_clips(station, detector)

        for clip in station_clips:
            clips[station.name][clip.start_time] = clip

        clip_count += len(clips[station.name])

    print(f'Found {clip_count} clips in the archive database.')
    print('')

    return clips


def get_stations():
    return Station.objects.all().order_by('id')


def get_detector(name):
    return Processor.objects.get(name=name)


def get_station_clips(station, detector):
    return Clip.objects.filter(
        station_id=station.id,
        creating_processor_id=detector.id,
        date__lt=CUTOFF_DATE
    ).order_by('start_time')


def show_archived_clips_not_in_file(clips, classifications):

    print('Looking for archive clips that are not in the file...')

    count = 0
    for station_name, station_clips in clips.items():
        start_times = sorted(station_clips.keys())
        for start_time in start_times:
            if start_time not in classifications[station_name]:
                # clip = station_clips[start_time]
                # print(f'  {station_name} {start_time} {clip.id}')
                count += 1

    print(f'Found {count} clips in the database that are not in the file.')
    print()


@transaction.atomic
def transfer_classifications(clips, classifications):

    print('Transferring classifications from file to archive database...')

    annotation_info = get_annotation_info(ANNOTATION_NAME)
    user = get_user(USER_NAME)

    clip_count = 0
    unclassified_clip_count = 0
    unlocated_clips = []

    for station_name, station_classifications in classifications.items():

        start_times = sorted(station_classifications.keys())

        for start_time in start_times:

            classification = station_classifications[start_time]

            if classification is None:
                unclassified_clip_count += 1
            
            else:

                clip = get_clip(station_name, start_time, clips)

                if clip is None:
                    unlocated_clips.append(
                        (station_name, start_time, classification))

                else:
                    # got clip

                    try:
                        classify_clip(clip, annotation_info, user, classification)

                    except Exception as e:
                        print(
                            f'Could not classify clip {clip.id} "{station_name}" '
                            f'{start_time} {classification}. Error message '
                            f'was: {e}')
                        print(
                            'Script will now exit with no changes to archive '
                            'database.')
                        raise

            clip_count += 1

            if clip_count % 1000 == 0:
                print(f'    {clip_count}...')

    classified_clip_count = clip_count - len(unlocated_clips)

    print(
        f'Transferred {classified_clip_count} classifications from file to '
        f'database.')
    
    print(f'{unclassified_clip_count} clips were unclassified.')

    print(f'Could not locate {len(unlocated_clips)} file clips in database:')
    for i, (station_name, start_time, classification) in \
            enumerate(unlocated_clips):
        start_time = start_time.astimezone(CENTRAL_TIME_ZONE)
        start_time = start_time.replace(tzinfo=None)
        print(f'    {i} {station_name} {str(start_time)} {classification}')

    print()


def get_clip(station_name, start_time, clips):

    clip = clips[station_name].get(start_time)

    if clip is None and station_name == 'Port Isabel' and \
            get_night(start_time) == '2025-04-26':
        # Clip is in file list for Port Isabel and is from the night
        # of 2025-04-26. Due to a drag and drop error, the clip may
        # actually be from Harlingen.
        
        # Look for database clip from Harlingen with same start time.
        clip = clips['Harlingen'].get(start_time)

    return clip


def get_night(start_time):
    local_time = start_time.astimezone(CENTRAL_TIME_ZONE)
    night = local_time.date()
    if local_time.hour < 12:
        night -= TimeDelta(days=1)
    return str(night)


def get_annotation_info(annotation_name):
    return AnnotationInfo.objects.get(name=annotation_name)


def get_user(user_name):
    return User.objects.get(username=user_name)


def classify_clip(clip, annotation_info, user, classification):

    creation_time = Datetime.now(UTC_TIME_ZONE)

    # print(
    #     f'Classifying clip {clip.id} {annotation_info.name} '
    #     f'{user.username} {str(creation_time)} {classification}...')

    kwargs = {
        'value': classification,
        'creation_time': creation_time,
        'creating_user': user,
        'creating_job': None,
        'creating_processor': None
    }

    StringAnnotation.objects.create(
        clip=clip,
        info=annotation_info,
        **kwargs)
            
    StringAnnotationEdit.objects.create(
        clip=clip,
        info=annotation_info,
        action=StringAnnotationEdit.ACTION_SET,
        **kwargs)


if __name__ == '__main__':
    main()
