"""
Processor that copies a clip audio file into a Vesper archive clip directory.
"""


import shutil

from lrgv.archiver.archiver_error import ArchiverError
from lrgv.dataflow import SimpleProcessor
import lrgv.util.vesper_utils as vesper_utils


class ClipAudioFileCopier(SimpleProcessor):


    def __init__(self, name, settings):
        super().__init__(name, settings)
        self._archive_dir_path = settings.archive_dir_path


    def _process_item(self, clip, finished):

        from_path = clip.audio_file_path

        # Get Vesper archive clip file path.
        clip_file_path = vesper_utils.get_clip_audio_file_path(clip.id)
        to_path = self._archive_dir_path / 'Clips' / clip_file_path

        try:
            to_path.parent.mkdir(mode=0o755, parents=True, exist_ok=True)
        except Exception as e:
            raise ArchiverError(
                f'Processor "{self.name}" could not create one or more '
                f'parent directories for clip audio file "{to_path}". '
                f'Error message was: {e}')

        try:
            shutil.copy2(from_path, to_path)
        except Exception as e:
            raise ArchiverError(
                f'Processor "{self.name}" could not copy file '
                f'"{from_path}" to "{to_path}". Error message was: {e}')
        
        return clip
