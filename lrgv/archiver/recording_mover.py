from lrgv.archiver.archiver_error import ArchiverError
from lrgv.dataflow import SimpleSink


class RecordingMover(SimpleSink):


    def _process_item(self, recording, finished):

        old_file_path = recording.metadata_file_path
        file_name = old_file_path.name
        new_file_path = self.settings.destination_dir_path / file_name

        try:
            new_file_path.parent.mkdir(mode=0o755, parents=True, exist_ok=True)
        except Exception as e:
            raise ArchiverError(
                f'Processor "{self.path}" could not create one or more '
                f'parent directories for recording file "{new_file_path}". '
                f'Error message was: {e}')

        try:
            old_file_path.rename(new_file_path)
        except Exception as e:
            raise ArchiverError(
                f'Processor "{self.path}" could not move file '
                f'"{old_file_path}" to "{new_file_path}". Error message '
                f'was: {e}')
