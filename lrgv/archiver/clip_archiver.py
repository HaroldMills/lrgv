from lrgv.archiver.archive_clip_creator import ArchiveClipCreator
from lrgv.archiver.file_lister import FileLister
from lrgv.dataflow import LinearGraph
from lrgv.util.bunch import Bunch


class ClipArchiver(LinearGraph):


    def _create_processors(self):

        s = self.settings

        name = f'{s.station_name} {s.detector_name} Clip Lister'
        settings = Bunch(
            dir_path=s.source_dir_path,
            file_name_re=s.clip_file_name_re,
            file_wait_period=s.clip_file_wait_period)
        lister = FileLister(name, settings)

        name = f'{s.station_name} {s.detector_name} Clip Creator'
        settings = Bunch(
            archive_url=s.archive_url,
            username=s.username,
            password=s.password)
        creator = ArchiveClipCreator(name, settings)

        return lister, creator
