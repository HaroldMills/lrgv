from dataflow import Processor
from dataflow.tests.processors import CollectingSink, RangeSource, Scaler
from dataflow.tests.processor_test_case import ProcessorTestCase
from vesper.util.bunch import Bunch


class ProcessorTests(ProcessorTestCase):
    
    
    def test_initialization(self):

        name = 'Bobo'
        settings = Bunch(scale_factor=2)
        p = Scaler(name, settings)

        self.assertEqual(p.name, name)
        self.assertEqual(p.settings, settings)
        self.assertEqual(len(p.input_ports), 1)
        self.assertEqual(len(p.output_ports), 1)
        self._assert_state(p, Processor.STATE_UNCONNECTED)


    def test_simple_graph(self):

        start = 0
        stop = 5
        chunk_size = 2
        scale_factor = 2

        settings = Bunch(start=start, stop=stop, chunk_size=chunk_size)
        source = RangeSource('Source', settings)

        settings = Bunch(scale_factor=scale_factor)
        scaler = Scaler('Scaler', settings)

        sink = CollectingSink('Sink')

        source.connect()
        scaler.connect({'Input': source.get_output_settings('Output')})
        sink.connect({'Input': scaler.get_output_settings('Output')})

        sink.start()
        scaler.start()
        source.start()

        while not sink.finished:
            output_data = source.process()
            input_data = {'Input': output_data['Output']}
            output_data = scaler.process(input_data)
            input_data = {'Input': output_data['Output']}
            sink.process(input_data)

        expected = list(range(start, stop * scale_factor, scale_factor))
        self.assertEqual(sink.items, expected)
