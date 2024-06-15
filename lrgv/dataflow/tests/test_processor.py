from lrgv.dataflow import Processor
from lrgv.dataflow.tests.processors import CollectingSink, RangeSource, Scaler
from lrgv.dataflow.tests.processor_test_case import ProcessorTestCase
from lrgv.util.bunch import Bunch


class ProcessorTests(ProcessorTestCase):
    
    
    def test_initialization(self):

        settings = Bunch(scale_factor=2)
        parent = None
        name = 'Bobo'
        p = Scaler(settings, parent, name)

        self.assertEqual(p.settings, settings)
        self.assertIsNone(p.parent)
        self.assertEqual(p.name, name)
        self.assertEqual(p.path, '/Bobo')
        self.assertEqual(len(p.input_ports), 1)
        self.assertEqual(len(p.output_ports), 1)
        self._assert_state(p, Processor.STATE_UNCONNECTED)


    def test_simple_graph(self):

        start = 0
        stop = 5
        chunk_size = 2
        scale_factor = 2

        settings = Bunch(start=start, stop=stop, chunk_size=chunk_size)
        source = RangeSource(settings, None, 'Source')

        settings = Bunch(scale_factor=scale_factor)
        scaler = Scaler(settings, None, 'Scaler')

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
