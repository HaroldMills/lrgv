from lrgv.dataflow import (
    LinearGraph, SimpleProcessor, SimpleProcessorMixin, SimpleSink,
    SimpleSource)
from lrgv.util.bunch import Bunch


class RangeSource(SimpleSource):


    def __init__(self, name, settings):
        super().__init__(name, settings)
        self._chunk_size = settings.chunk_size
        self._next_value = settings.start
        self._stop_value = settings.stop


    def _process_items(self):
    
        start_value = self._next_value
        stop_value = min(start_value + self._chunk_size, self._stop_value)
        items = tuple(range(start_value, stop_value))

        self._next_value = stop_value
        finished = self._next_value == self._stop_value

        return items, finished
    

class CollectingSink(SimpleSink):


    def __init__(self, name):
        super().__init__(name)
        self._items = []


    @property
    def items(self):
        return self._items
    
    
    def _process_items(self, items, finished):
        self._items += items


class Scaler(SimpleProcessor):


    def __init__(self, name, settings):
        super().__init__(name, settings)
        self._scale_factor = settings.scale_factor


    def _process_item(self, item, finished):
        return self._scale_factor * item


class Offsetter(SimpleProcessor):


    def __init__(self, name, settings):
        super().__init__(name, settings)
        self._offset = settings.offset


    def _process_item(self, item, finished):
        return item + self._offset


class AffineTransformer(SimpleProcessorMixin, LinearGraph):


    def _create_processors(self):

        s = self.settings

        settings = Bunch(scale_factor=s.scale_factor)
        scaler = Scaler('Scaler', settings)

        settings = Bunch(offset=s.offset)
        offsetter = Offsetter('Offsetter', settings)

        return scaler, offsetter
