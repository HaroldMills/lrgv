import re
import time

from lrgv.archiver.recording import Recording
from lrgv.dataflow import SimpleSource
from lrgv.util.bunch import Bunch


_RECORDING_METADATA_FILE_NAME_RE = re.compile(
    r'^'
    r'(?P<station_name>.+)'
    f'_'
    r'(?P<year>\d\d\d\d)-(?P<month>\d\d)-(?P<day>\d\d)'
    r'_'
    r'(?P<hour>\d\d)\.(?P<minute>\d\d)\.(?P<second>\d\d)'
    r'_'
    r'Z'
    r'\.(?:json|JSON)'
    r'$')


class RecordingLister(SimpleSource):


    def _process_items(self):

        s = self.settings

        # Start with all file paths, sorted lexicographically.
        file_paths = tuple(sorted(p for p in s.recording_dir_path.glob('*')))

        # Exclude files that aren't recording metadata files.
        files = self._get_matching_files(file_paths)

        # If indicated, exclude files that were modified too recently.
        if s.recording_file_wait_period is not None:
            files = tuple(
                f for f in files
                if _time_from_last_mod(f.path) >= s.recording_file_wait_period)

        # Create recordings.
        recordings = tuple(Recording(f.path) for f in files)

        return recordings, False


    def _get_matching_files(self, file_paths):

            files = []

            for p in file_paths:

                m = _RECORDING_METADATA_FILE_NAME_RE.match(p.name)

                if m is not None:
                    files.append(Bunch(path=p, name_match=m))

            return tuple(files)
    

def _time_from_last_mod(file_path):
    return time.time() - file_path.stat().st_mtime
