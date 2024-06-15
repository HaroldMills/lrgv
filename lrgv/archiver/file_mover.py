from lrgv.archiver.archiver_error import ArchiverError
from lrgv.dataflow import SimpleSink


class FileMover(SimpleSink):


    def _process_item(self, file, finished):

        new_path = self.settings.destination_dir_path / file.path.name

        try:
            file.path.rename(new_path)
        except Exception as e:
            raise ArchiverError(
                f'Processor "{self.path}" could not move file '
                f'"{file.path}" to "{new_path}". Error message '
                f'was: {e}')
