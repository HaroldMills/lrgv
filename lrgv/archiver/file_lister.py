import re
import time

from lrgv.dataflow import SimpleSource
from lrgv.util.bunch import Bunch


class FileLister(SimpleSource):


    def __init__(self, settings, parent=None, name=None):

        super().__init__(settings, parent, name)

        self._dir_path = settings.dir_path

        if settings.file_name_re is None:
            self._file_name_re = None
        else:
            self._file_name_re = re.compile(settings.file_name_re)

        self._file_wait_period = settings.file_wait_period


    def _process_items(self):

        # Start with all file paths, sorted lexicographically.
        file_paths = tuple(sorted(p for p in self._dir_path.glob('*')))

        # If indicated, output only files whose names are matched by
        # `self._file_name_re`.
        files = self._get_matching_files(file_paths)

        # If indicated, output only files that were last modified at
        # least `self._wait_period` seconds ago.
        if self._file_wait_period is not None:
            mod_time_threshold = time.time() - self._file_wait_period
            files = tuple(
                f for f in files
                if f.path.stat().st_mtime <= mod_time_threshold)
            
        return files, False
    

    def _get_matching_files(self, file_paths):

        if self._file_name_re is None:
            # not filtering files by name

            return tuple(Bunch(path=p, name_match=None) for p in file_paths)
        
        else:
            # filtering files by name

            files = []

            for p in file_paths:

                m = self._file_name_re.match(p.name)

                if m is not None:
                    files.append(Bunch(path=p, name_match=m))

            return tuple(files)
