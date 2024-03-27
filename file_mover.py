import logging

from dataflow import InputPort, Processor


_logger = logging.getLogger()


class FileMover(Processor):


    type_name = 'File Mover'


    def __init__(self, name, settings):
        super().__init__(name, settings)
        self._destination_dir_path = settings.destination_dir_path


    def _create_input_ports(self):
        return (InputPort(self),)
    

    def _process(self, input_data):

        for file_path in input_data['Input'].items:

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

        return {}
