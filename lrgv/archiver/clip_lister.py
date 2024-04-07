from lrgv.archiver.clip import Clip
from lrgv.archiver.file_lister import FileLister
from lrgv.dataflow import LinearGraph, SimpleProcessor, SimpleSourceMixin
from lrgv.util.bunch import Bunch


class _ClipCreator(SimpleProcessor):

    def _process_item(self, audio_file_path, finished):
        return Clip(audio_file_path)


class ClipLister(SimpleSourceMixin, LinearGraph):


    def _create_processors(self):

        s = self.settings

        name = f'{self.name} - File Lister'
        settings = Bunch(
            dir_path=s.clip_dir_path,
            file_name_re=s.clip_file_name_re,
            file_wait_period=s.clip_file_wait_period)
        lister = FileLister(name, settings)

        name = f'{self.name} - Clip Object Creator'
        creator = _ClipCreator(name)

        return lister, creator
