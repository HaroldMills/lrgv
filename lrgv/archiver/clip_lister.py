from zoneinfo import ZoneInfo

from lrgv.archiver.clip import Clip
from lrgv.archiver.file_lister import FileLister
from lrgv.dataflow import LinearGraph, SimpleProcessor, SimpleSourceMixin
from lrgv.util.bunch import Bunch


_CLIP_METADATA_FILE_NAME_RE = (
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
    r'\.(?:json|JSON)'
    r'$')


_UTC = ZoneInfo('UTC')


class _ClipCreator(SimpleProcessor):

    def _process_item(self, metadata_file, finished):
        return Clip(metadata_file.path)


class ClipLister(SimpleSourceMixin, LinearGraph):


    def _create_processors(self):

        s = self.settings

        name = f'{self.name} - File Lister'
        settings = Bunch(
            dir_path=s.clip_dir_path,
            file_name_re=_CLIP_METADATA_FILE_NAME_RE,
            file_wait_period=s.clip_file_wait_period)
        lister = FileLister(name, settings)

        name = f'{self.name} - Clip Object Creator'
        creator = _ClipCreator(name)

        return lister, creator
