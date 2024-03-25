from dataflow import Data, Graph, InputPort, OutputPort, Processor
from vesper.util.bunch import Bunch


class RangeSource(Processor):


    type_name = 'Integer Range Source'


    def __init__(self, name, settings):
        super().__init__(name, settings)
        self._chunk_size = settings.chunk_size
        self._next_value = settings.start
        self._stop_value = settings.stop


    def _create_output_ports(self):
        return (OutputPort(self),)


    def _process(self, input_data):

        start_value = self._next_value
        stop_value = min(start_value + self._chunk_size, self._stop_value)
        items = tuple(range(start_value, stop_value))

        self._next_value = stop_value

        finished = self._next_value == self._stop_value

        if finished:
            self._state = Processor.STATE_FINISHED

        output = Data(items, finished)
        return {'Output': output}
    

class CollectingSink(Processor):


    type_name = 'CollectingSink'


    def __init__(self, name):
        super().__init__(name)
        self._items = []


    def _create_input_ports(self):
        return (InputPort(self),)

    
    @property
    def items(self):
        return self._items
    
    
    def _process(self, input_data):
        input = input_data['Input']
        self._items += input.items
        if input.finished:
            self._state = Processor.STATE_FINISHED
        return {}


class Scaler(Processor):


    type_name = 'Scaler'


    def __init__(self, name, settings):
        super().__init__(name, settings)
        self._scale_factor = settings.scale_factor


    def _create_input_ports(self):
        return (InputPort(self),)

    
    def _create_output_ports(self):
        return (OutputPort(self),)


    def _process(self, input_data):

        input = input_data['Input']
        items = tuple(i * self._scale_factor for i in input.items)

        if input.finished:
            self._state = Processor.STATE_FINISHED

        output = Data(items, input.finished)
        return {'Output': output}


class Offsetter(Processor):


    type_name = 'Offsetter'


    def __init__(self, name, settings):
        super().__init__(name, settings)
        self._offset = settings.offset


    def _create_input_ports(self):
        return (InputPort(self),)

    
    def _create_output_ports(self):
        return (OutputPort(self),)


    def _process(self, input_data):

        input = input_data['Input']
        items = tuple(i + self._offset for i in input.items)

        if input.finished:
            self._state = Processor.STATE_FINISHED

        output = Data(items, input.finished)
        return {'Output': output}


class AffineTransformer(Graph):


    type_name = 'Affine Transformer'


    def _create_input_ports(self):
        return (InputPort(self),)

    
    def _create_output_ports(self):
        return (OutputPort(self),)


    def _create_processors(self):

        s = self.settings

        settings = Bunch(scale_factor=s.scale_factor)
        scaler = Scaler('Scaler', settings)

        settings = Bunch(offset=s.offset)
        offsetter = Offsetter('Offsetter', settings)

        return (scaler, offsetter)
