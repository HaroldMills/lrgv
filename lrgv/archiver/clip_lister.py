from datetime import datetime as DateTime
from zoneinfo import ZoneInfo

from lrgv.archiver.clip import Clip
from lrgv.archiver.file_lister import FileLister
from lrgv.dataflow import LinearGraph, SimpleProcessor, SimpleSourceMixin
from lrgv.util.bunch import Bunch


_CLIP_FILE_NAME_RE = (
    r'^'
    r'(?P<station_name>.+)'
    f'_'
    r'(?P<year>\d\d\d\d)-(?P<month>\d\d)-(?P<day>\d\d)'
    r'_'
    r'(?P<hour>\d\d)\.(?P<minute>\d\d)\.(?P<second>\d\d).(?P<millis>\d\d\d)'
    r'_'
    r'Z'
    r'_'
    r'(?P<num>\d\d)'
    r'\.(?:wav|WAV)'
    r'$')


_UTC = ZoneInfo('UTC')


class _ClipCreator(SimpleProcessor):

    def _process_item(self, audio_file, finished):

        audio_file_path = audio_file.path

        match = audio_file.name_match
        station_name = match.group('station_name')
        start_time = _get_clip_start_time(match)

        return Clip(audio_file_path, station_name, start_time)


def _get_clip_start_time(match):

    group = match.group

    def get(field_name):
        return int(group(field_name))

    year = get('year')
    month = get('month')
    day = get('day')
    hour = get('hour')
    minute = get('minute')
    second = get('second')
    millis = get('millis')
    num = get('num')

    micros = 1000 * (millis + num)

    start_time = DateTime(
        year, month, day, hour, minute, second, micros, _UTC)

    return start_time


class ClipLister(SimpleSourceMixin, LinearGraph):


    def _create_processors(self):

        s = self.settings

        name = f'{self.name} - File Lister'
        settings = Bunch(
            dir_path=s.clip_dir_path,
            file_name_re=_CLIP_FILE_NAME_RE,
            file_wait_period=s.clip_file_wait_period)
        lister = FileLister(name, settings)

        name = f'{self.name} - Clip Object Creator'
        creator = _ClipCreator(name)

        return lister, creator
