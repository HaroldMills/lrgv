import logging

from lrgv.dataflow import SimpleSink


_logger = logging.getLogger(__name__)


class FileDeleter(SimpleSink):

    def _process_item(self, file, finished):
        _logger.info(f'Processor "{self.path}" deleting file "{file.path}"...')
        file.path.unlink()
