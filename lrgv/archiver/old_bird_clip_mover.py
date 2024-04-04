from lrgv.archiver.file_lister import FileLister
from lrgv.archiver.file_mover import FileMover
from lrgv.dataflow import LinearGraph
from lrgv.util.bunch import Bunch


class OldBirdClipMover(LinearGraph):


    def _create_processors(self):

        s = self.settings

        name = f'{s.station_name} Old Bird Clip Lister'
        settings = Bunch(
            dir_path=s.source_dir_path,
            file_name_re=s.clip_file_name_re,
            file_wait_period=s.clip_file_wait_period)
        lister = FileLister(name, settings)

        name = f'{s.station_name} Old Bird Clip Processor'
        settings = Bunch(destination_dir_path=s.destination_dir_path)
        mover = FileMover(name, settings)

        return lister, mover
