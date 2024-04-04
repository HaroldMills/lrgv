import logging

from lrgv.dataflow import SimpleSink


_logger = logging.getLogger(__name__)


class FileMover(SimpleSink):


    def __init__(self, name, settings):
        super().__init__(name, settings)
        self._destination_dir_path = settings.destination_dir_path


    def _process_item(self, file_path, finished):

        new_path = self._destination_dir_path / file_path.name

        _logger.info(
            f'Processor "{self.name}" moving file "{file_path}" '
            f'to "{new_path}"...')

        # try:
        #     file_path.replace(new_path)
        # except Exception as e:
        #     _logger.warning(
        #         f'File mover "{self.name}" could not move file '
        #         f'"{file_path}" to "{new_path}". Error message '
        #         f'was: {e}')
