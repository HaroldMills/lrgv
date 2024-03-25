from dataflow import Processor
from vesper.tests.test_case import TestCase


class ProcessorTestCase(TestCase):


    def _assert_state(self, processor, expected):

        state = processor.state

        self.assertEqual(state, expected)

        self.assertEqual(
            processor.unconnected, state == Processor.STATE_UNCONNECTED)
        
        self.assertEqual(
            processor.connected, state == Processor.STATE_CONNECTED)
        
        self.assertEqual(
            processor.running, state == Processor.STATE_RUNNING)
        
        self.assertEqual(
            processor.finished, state == Processor.STATE_FINISHED)
