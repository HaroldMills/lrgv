from lrgv.archiver.file_lister import FileLister
from lrgv.archiver.file_mover import FileMover
from lrgv.dataflow import LinearGraph
from lrgv.util.bunch import Bunch


_DETECTOR_NAME = 'Dick'

_CLIP_FILE_NAME_RE = (
    r'^'
    r'Dick_'
    r'(?P<year>\d\d\d\d)-(?P<month>\d\d)-(?P<day>\d\d)'
    r'_'
    r'(?P<hour>\d\d)\.(?P<minute>\d\d)\.(?P<second>\d\d)'
    r'_'
    r'(?P<num>\d\d)'
    r'\.(?:wav|WAV)'
    r'$')


class OldBirdClipConverter(LinearGraph):


    def _create_processors(self):

        s = self.settings

        name = f'{s.station_name} Old Bird Clip File Lister'
        settings = Bunch(
            dir_path=s.clip_dir_path,
            file_name_re=_CLIP_FILE_NAME_RE,
            file_wait_period=s.clip_file_wait_period)
        lister = FileLister(name, settings)

        # TODO: Replace file mover with processor that converts and
        # moves clip.
        name = f'{s.station_name} Old Bird Clip File Converter'
        paths = s.station_paths.detectors[_DETECTOR_NAME]
        settings = Bunch(destination_dir_path=paths.incoming_clip_dir_path)
        mover = FileMover(name, settings)

        return lister, mover
