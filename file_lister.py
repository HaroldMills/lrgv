import re
import time

from dataflow import Data, OutputPort, Processor


class FileLister(Processor):


    type_name = 'File Lister'


    def __init__(self, name, settings):

        super().__init__(name, settings)

        self._dir_path = settings.dir_path

        if settings.file_name_re is None:
            self._file_name_re = None
        else:
            self._file_name_re = re.compile(settings.file_name_re)

        self._file_wait_period = settings.file_wait_period


    def _create_output_ports(self):
        return (OutputPort(self),)
    

    def _process(self, input_data):

        # Start with all file paths.
        file_paths = tuple(p for p in self._dir_path.glob('*'))

        # If indicated, output only files whose names are matched by
        # `self._file_name_re`.
        if self._file_name_re is not None:
            file_paths = tuple(
                p for p in file_paths
                if self._file_name_re.match(p.name) is not None)

        # If indicated, output only files that were last modified at
        # least `self._wait_period` seconds ago.
        if self._file_wait_period is not None:
            mod_time_threshold = time.time() - self._file_wait_period
            file_paths = tuple(
                p for p in file_paths
                if p.stat().st_mtime <= mod_time_threshold)
            
        return {'Output': Data(file_paths, False)}
