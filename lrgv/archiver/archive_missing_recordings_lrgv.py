"""
Archives LRGV Vesper Recorder recordings that have not already been
archived with clips.

Most Vesper Recorder recordings are archived with Nighthawk clips, but
recordings in which Nighthawk does not produce any clips are not archived
in this way. This script identifies such recordings and archives them.
"""


# TODO: Consider splitting this script into two scripts, one that
# writes a JSON metadata file for the recordings that need to be
# archived, and another that reads the JSON metadata file and archives
# the recordings.

# TODO: This script attempts to use both the `lrgv` and `vesper` packages.
# This is problematic since the `lrgv` package requires Python 3.13 while
# the `vespeer` package requires Python 3.10. I will either need to:
# 
#     1. Modify the `lrgv` package to use Python 3.10 or so this script
#        can use both the `lrgv` and `vesper` packages.
#
#     2. Add a `get_recording_metadata` Django view to Vesper so this
#        script can avoid using the `vesper` package.
#
# The second option is preferable in a way, since we want scripts to use
# the Vesper web API rather than the `vesper` package's Django ORM to
# interact with Vesper archives, and I don't like the idea of limiting
# the `lrgv` package to using Python 3.10. However, adding an ad-hoc
# `get_recording_metadata` Django view to Vesper doesn't really move us
# in the direction of a complete, well-designed, and well-documented
# Vesper web API in any significant way.


from datetime import datetime as Datetime
import csv
import datetime
import json

import requests

# Set up Django. This must happen before any use of Django, including
# ORM class imports.
import vesper.util.django_utils as django_utils
django_utils.set_up_django()

from lrgv.archiver.archiver_error import ArchiverError
from lrgv.archiver.app_settings_lrgv import app_settings
from vesper.django.app.models import Recording
from vesper.util.bunch import Bunch


'''
Example recording JSON:

{
    "recordings": [
        {
            "station": "Alamo",
            "recorder": "Vesper Recorder 0",
            "mic_outputs": [
                "21c 0 Vesper Output"
            ],
            "start_time": "2025-05-30 01:49:23 Z",
            "length": 662977350,
            "sample_rate": 22050
        }
    ]
}
'''


STATION_NAMES = (
    'Alamo',
    'Donna',
    'Harlingen',
    'Port Isabel',
    'Rio Hondo',
    'Roma HS',
    'Roma RBMS',
    'Rio Grande City'
)

STATION_NUMS = {n: i for i, n in enumerate(STATION_NAMES)}

FILE_LIST_STATION_NAME_CORRECTIONS = {'Roma': 'Roma HS'}

FILE_PATH_FORMAT = (
    '/Users/harold/Desktop/NFC/Data/Old Bird/LRGV/2025/Station Data/'
    'Active/LRGV - {}/Apps/Vesper Recorder/Recording Files.csv')

CHANNEL_COUNT = 1
SAMPLE_RATE = 22050

# Format for Vesper server login URL. We set the URL to redirect to
# "/health-check/" after login instead of the default "/" since "/"
# redirects to the clip calendar, which is relatively expensive to
# serve.
LOGIN_URL_SUFFIX_FORMAT = '{}login/?next={}health-check/'

CREATE_CLIPS_URL_SUFFIX = 'import-recordings-and-clips/'


def main():

    db_recordings = get_database_recordings()

    listed_recordings = get_listed_recordings()

    # Show recordings in database but not in file lists.
    compare_recordings(
        db_recordings, 'database', listed_recordings, 'file lists')
    
    # Show recordings in file lists but not in database.
    compare_recordings(
        listed_recordings, 'file lists', db_recordings, 'database')
    
    # Archive recordings in file lists but not in database.
    # archiver = Archiver()
    # missing_recordings = sorted(listed_recordings - db_recordings)
    # archiver.archive_recordings(missing_recordings)


def compare_recordings(set_a, name_a, set_b, name_b):
    print(f'Recordings in {name_a} but not {name_b}:')
    recordings = sorted(set_a - set_b)
    for r in recordings:
        print(f'    {r}')


def get_database_recordings():

    def get_recording(r):
        check_recording_attribute(r, 'num_channels', CHANNEL_COUNT)
        check_recording_attribute(r, 'sample_rate', SAMPLE_RATE)
        return r.station.name, r.start_time, r.length

    return frozenset(
        get_recording(r)
        for r in Recording.objects.select_related(
            'station', 'recorder').filter(
            recorder__name__startswith='Vesper Recorder'))


def check_recording_attribute(r, attribute_name, expected_value):
    
    value = getattr(r, attribute_name)

    if value != expected_value:

        raise ValueError(
            f'Unexpected {attribute_name} {value} for '
            f'recording {r.id} "{r.station_name}" {r.start_time}. '
            f'Expected {expected_value}.')


def get_listed_recordings():

    recordings = list()

    for station_name in STATION_NAMES:

        file_path = FILE_PATH_FORMAT.format(station_name)

        with open(file_path, 'r', newline='') as file:

            reader = csv.reader(file)

            # Skip header.
            next(reader)

            for row in reader:
                recording = parse_list_row(row)
                recordings.append(recording)

    return frozenset(recordings)


def parse_list_row(row):

    # Get '_'-separated file name parts.
    file_name = row[0].split('\\')[-1]
    parts = file_name.split('_')

    # Get station name.
    station_name = parts[0]
    station_name = \
        FILE_LIST_STATION_NAME_CORRECTIONS.get(station_name, station_name)

    # Get recording start time.
    date = parts[1]
    time = parts[2].replace('.', ':')
    start_time = Datetime.strptime(f'{date} {time}', '%Y-%m-%d %H:%M:%S')
    start_time = start_time.replace(tzinfo=datetime.timezone.utc)
    
    # Get other recording information.
    channel_count = int(row[1])
    sample_rate = int(row[2])
    length = int(row[3])

    r = Bunch(
        station_name=station_name,
        channel_count=channel_count,
        start_time=start_time,
        length=length,
        sample_rate=sample_rate)
    
    check_recording_attribute(r, 'channel_count', CHANNEL_COUNT)
    check_recording_attribute(r, 'sample_rate', SAMPLE_RATE)

    return r.station_name, r.start_time, r.length


class Archiver:


    def __init__(self):

        s = app_settings.vesper

        self._login_url = \
            LOGIN_URL_SUFFIX_FORMAT.format(s.archive_url, s.archive_url_base)
        self._create_clips_url = s.archive_url + CREATE_CLIPS_URL_SUFFIX

        self._username = s.username
        self._password = s.password
        self._session = None


    def archive_recordings(self, recordings):

        metadata = create_recording_metadata_json(recordings)

        if self._session is None:
            self._start_new_session()

        response = post(self._session, self._create_clips_url, json=metadata)

        if not response.ok:
            message = response.content.decode(response.encoding)
            raise ArchiverError(
                f'Could not create missing recordings in Vesper archive '
                f'database. Vesper server error message was: {message}')

        else:
            print('Created missing recordings in Vesper archive.')


    def _start_new_session(self):

        if self._session is not None:
            self._session.close()

        self._session = requests.session()

        try:
            self._get_csrf_token()
        except Exception:
            self._session = None
            raise

        self._log_in()


    def _get_csrf_token(self):

        # Send GET request to Vesper server login page so HTTP session
        # will have Django CSRF token. The token is required for
        # subsequent POST requests that log in to the Vesper server and
        # create clips.
        try:
            response = self._session.get(self._login_url)
        except Exception as e:
            raise ArchiverError(
                f'Could not get CSRF token from Vesper server. HTTP GET '
                f'request raised exception with message: {e}')

        if not response.ok:
            raise ArchiverError(
                f'Could not get CSRF token from Vesper server. HTTP GET '
                f'request returned status code {response.status_code}')


    def _log_in(self):

        data = {
            'username': self._username,
            'password': self._password
        }

        response = post(self._session, self._login_url, data=data)

        if not response.ok:
            raise ArchiverError('Could not log in to Vesper server.')
        

def create_recording_metadata_json(recordings):
    recording_dicts = [create_recording_dict(r) for r in recordings]
    d = {'recordings': recording_dicts}
    return json.dumps(d, indent=4)


def create_recording_dict(r):

    station_name, start_time, length = r

    station_num = STATION_NUMS[station_name]
    recorder_name = f'Vesper Recorder {station_num}'
    mic_output_name = f'21c {station_num} Vesper Output'

    start_time = start_time.strftime('%Y-%m-%d %H:%M:%S Z')

    return {
        'station': station_name,
        'recorder': recorder_name,
        'mic_outputs': [mic_output_name],
        'start_time': start_time,
        'length': length,
        'sample_rate': SAMPLE_RATE
    }


def post(session, url, **kwargs):
    headers = get_post_headers(session)
    return session.post(url, headers=headers, **kwargs)


def get_post_headers(session):
    return {'X-CSRFToken': session.cookies['csrftoken']}


if __name__ == '__main__':
    main()
