import logging

from lrgv.archiver.file_lister import FileLister
from lrgv.dataflow import LinearGraph, SimpleSink
from lrgv.util.bunch import Bunch


_logger = logging.getLogger(__name__)


_DETECTOR_NAME = 'Dick'

_CLIP_FILE_NAME_RE = (
    r'^'
    f'{_DETECTOR_NAME}_'
    r'(?P<year>\d\d\d\d)-(?P<month>\d\d)-(?P<day>\d\d)'
    r'_'
    r'(?P<hour>\d\d)\.(?P<minute>\d\d)\.(?P<second>\d\d)'
    r'_'
    r'(?P<num>\d\d)'
    r'\.(?:wav|WAV)'
    r'$')


class OldBirdClipDeleter(LinearGraph):


    def _create_processors(self):

        s = self.settings

        settings = Bunch(
            dir_path=s.source_clip_dir_path,
            file_name_re=_CLIP_FILE_NAME_RE,
            file_wait_period=s.clip_file_wait_period)
        lister = FileLister(settings, self)

        deleter = _ClipFileDeleter(settings, self)

        return lister, deleter


class _ClipFileDeleter(SimpleSink):


    def _process_item(self, audio_file, finished):

        _logger.info(
            f'Processor "{self.path}" deleting file "{audio_file.path}"...')

        audio_file.path.unlink()
