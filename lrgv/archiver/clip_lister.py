import re
import time

from lrgv.archiver.clip import Clip
from lrgv.dataflow import SimpleSource
from lrgv.util.bunch import Bunch


_CLIP_METADATA_FILE_NAME_RE = re.compile(
    r'^'
    r'(?P<station_name>.+)'
    f'_'
    r'(?P<year>\d\d\d\d)-(?P<month>\d\d)-(?P<day>\d\d)'
    r'_'
    r'(?P<hour>\d\d)\.(?P<minute>\d\d)\.(?P<second>\d\d).(?P<millis>\d\d\d)'
    r'_'
    r'Z'
    r'_'
    r'(?P<num>\d\d)'
    r'\.(?:json|JSON)'
    r'$')

_AUDIO_FILE_NAME_EXTENSION = '.wav'


class ClipLister(SimpleSource):


    def _process_items(self):

        s = self.settings

        # Start with all file paths, sorted lexicographically.
        file_paths = tuple(sorted(p for p in s.clip_dir_path.glob('*')))

        # Exclude files that aren't clip metadata files.
        files = self._get_matching_files(file_paths)

        # If indicated, exclude files that were modified too recently.
        if s.clip_file_wait_period is not None:
            files = tuple(
                f for f in files
                if _time_from_last_mod(f.path) >= s.clip_file_wait_period)
            
        # Exclude files that don't have a matching audio file.
        files = tuple(f for f in files if self._has_matching_audio_file(f))

        # Create clips.
        clips = tuple(Clip(f.path) for f in files)
            
        return clips, False
    

    def _get_matching_files(self, file_paths):

            files = []

            for p in file_paths:

                m = _CLIP_METADATA_FILE_NAME_RE.match(p.name)

                if m is not None:
                    files.append(Bunch(path=p, name_match=m))

            return tuple(files)
    

    def _has_matching_audio_file(self, file):

        audio_file_path = file.path.with_suffix(_AUDIO_FILE_NAME_EXTENSION)

        # Check that audio file exists.
        if not audio_file_path.exists():
            return False
        
        # If indicated, check that audio file was not modified too recently.
        wait_period = self.settings.clip_file_wait_period
        if wait_period is not None and \
                _time_from_last_mod(audio_file_path) < wait_period:
            return False
            
        return True


def _time_from_last_mod(file_path):
    return time.time() - file_path.stat().st_mtime
