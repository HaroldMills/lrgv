from dataflow import LinearGraph
from file_lister import FileLister
from file_mover import FileMover
from vesper.util.bunch import Bunch


class OldBirdClipMover(LinearGraph):


    type_name = 'Old Bird Clip Processor'


    def _create_processors(self):

        s = self.settings

        name = f'{s.station_name} Old Bird Clip Lister'
        settings = Bunch(
            dir_path=s.source_dir_path,
            file_name_re=s.clip_file_name_re,
            file_wait_period=s.clip_file_wait_period)
        source = FileLister(name, settings)

        name = f'{s.station_name} Old Bird Clip Processor'
        settings = Bunch(destination_dir_path=s.destination_dir_path)
        mover = FileMover(name, settings)

        return source, mover
