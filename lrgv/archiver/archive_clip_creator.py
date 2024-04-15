import logging

from lrgv.dataflow import SimpleSink


_logger = logging.getLogger(__name__)


class ArchiveClipCreator(SimpleSink):


    def _process_item(self, clip, finished):

        _logger.info(
            f'Processor "{self.name}" received clip '
            f'"{clip.audio_file_path}" for station "{clip.station_name}", '
            f'start time {clip.start_time}.')

        # TODO: Put clip into Vesper archive, set its ID, and pass it on.
         
        # try:
        #     file_path.replace(new_path)
        # except Exception as e:
        #     _logger.warning(
        #         f'File mover "{self.name}" could not move file '
        #         f'"{file_path}" to "{new_path}". Error message '
        #         f'was: {e}')
