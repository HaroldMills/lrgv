from lrgv.archiver.archiver_error import ArchiverError
from lrgv.dataflow import SimpleSink


class ClipMover(SimpleSink):


    def __init__(self, name, settings):
        super().__init__(name, settings)
        self._destination_dir_path = settings.destination_dir_path


    def _process_item(self, clip, finished):
        self._move_clip_file(clip.audio_file_path)
        self._move_clip_file(clip.metadata_file_path)
        

    def _move_clip_file(self, file_path):

        new_path = self._destination_dir_path / file_path.name

        try:
            file_path.rename(new_path)
        except Exception as e:
            raise ArchiverError(
                f'Processor "{self.name}" could not move file '
                f'"{file_path}" to "{new_path}". Error message '
                f'was: {e}')
