from lrgv.archiver.archiver_error import ArchiverError
from lrgv.dataflow import SimpleSink


class ClipMover(SimpleSink):


    def _process_item(self, clip, finished):
        self._move_clip_file(clip.audio_file_path)
        self._move_clip_file(clip.metadata_file_path)
        

    def _move_clip_file(self, file_path):

        new_path = self.settings.destination_dir_path / file_path.name

        try:
            new_path.parent.mkdir(mode=0o755, parents=True, exist_ok=True)
        except Exception as e:
            raise ArchiverError(
                f'Processor "{self.path}" could not create one or more '
                f'parent directories for clip audio file "{new_path}". '
                f'Error message was: {e}')

        try:
            file_path.rename(new_path)
        except Exception as e:
            raise ArchiverError(
                f'Processor "{self.path}" could not move file '
                f'"{file_path}" to "{new_path}". Error message '
                f'was: {e}')
