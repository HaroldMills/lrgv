from lrgv.archiver.file_deleter import FileDeleter
from lrgv.archiver.file_lister import FileLister
from lrgv.dataflow import LinearGraph
from lrgv.util.bunch import Bunch


class OldBirdClipDeleter(LinearGraph):


    def _create_processors(self):

        s = self.settings

        settings = Bunch(
            dir_path=s.source_clip_dir_path,
            file_name_re=s.clip_file_name_re,
            recursive=False,
            file_wait_period=s.clip_file_wait_period)
        lister = FileLister(settings, self)

        deleter = FileDeleter(settings, self)

        return lister, deleter
