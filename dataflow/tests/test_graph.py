from dataflow import LinearGraph, Processor
from dataflow.tests.processors import (
    AffineTransformer, CollectingSink, RangeSource, Scaler)
from dataflow.tests.processor_test_case import ProcessorTestCase
from vesper.util.bunch import Bunch


class TestGraph(LinearGraph):


    def __init__(self, name, source_settings, processor):
        self._processor = processor
        super().__init__(name, source_settings)


    def _create_processors(self):
        source = RangeSource('Source', self.settings)
        sink = CollectingSink('Sink')
        return source, self._processor, sink
    

    @property
    def items(self):
        sink = self._processors[2]
        return sink.items


class ProcessorGraphTests(ProcessorTestCase):
    
    
    def test_unnested_graph(self):

        source_settings = Bunch(start=0, stop=5, chunk_size=2)
        scale_factor = 2

        scaler_settings = Bunch(scale_factor=scale_factor)
        scaler = Scaler('Scaler', scaler_settings)
        
        graph = TestGraph('Test Graph', source_settings, scaler)

        s = source_settings
        expected_items = \
            list(range(s.start, s.stop * scale_factor, scale_factor))
        
        self._test_graph(graph, expected_items)


    def _test_graph(self, graph, expected_items):

        self._assert_state(graph, Processor.STATE_UNCONNECTED)

        graph.connect()
        self._assert_state(graph, Processor.STATE_CONNECTED)

        graph.start()
        self._assert_state(graph, Processor.STATE_RUNNING)

        while not graph.finished:
            self._assert_state(graph, Processor.STATE_RUNNING)
            graph.process()

        self._assert_state(graph, Processor.STATE_FINISHED)
            
        self.assertEqual(graph.items, expected_items)


    def test_nested_graph(self):

        source_settings = Bunch(start=0, stop=5, chunk_size=2)
        scale_factor = 2
        offset = 1
        
        transformer_settings = Bunch(
            scale_factor=scale_factor,
            offset=offset)
        transformer = AffineTransformer('Transformer', transformer_settings)

        graph = TestGraph('Test Graph', source_settings, transformer)

        s = source_settings
        start = s.start + offset
        stop = s.stop * scale_factor + offset
        expected_items = list(range(start, stop, scale_factor))
        
        self._test_graph(graph, expected_items)

