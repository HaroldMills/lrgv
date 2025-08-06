from datetime import datetime as DateTime
from pathlib import Path

from lrgv.archiver.recording import Recording
from lrgv.util.test_case import TestCase


_DATA_DIR_PATH = Path(__file__).parent / 'data'
_EXPECTED_STATION_NAME = 'Alamo'
_EXPECTED_MIC_OUTPUT_NAMES = ['21c 0 Vesper Output']
_EXPECTED_START_TIME = DateTime.fromisoformat("2025-08-05T02:00:00.000Z")
_EXPECTED_LENGTH = 692568450
_EXPECTED_SAMPLE_RATE = 22050
_EXPECTED_ID = 1234


class RecordingTests(TestCase):
    
    
    def test_initialization_0(self):

        """Tests initialization of a `Recording` with no ID."""

        metadata_file_path = _create_metadata_file_path(0)
        recording = Recording(metadata_file_path)

        self._check_constant_attributes(recording)
        self.assertEqual(recording.metadata_file_path, metadata_file_path)
        self.assertIsNone(recording.id)


    def _check_constant_attributes(self, recording):
        self.assertEqual(recording.station_name, _EXPECTED_STATION_NAME)
        self.assertEqual(
            recording.mic_output_names, _EXPECTED_MIC_OUTPUT_NAMES)
        self.assertEqual(recording.start_time, _EXPECTED_START_TIME)
        self.assertEqual(recording.length, _EXPECTED_LENGTH)
        self.assertEqual(recording.sample_rate, _EXPECTED_SAMPLE_RATE)


    def test_initialization_1(self):

        """Tests initialization of a `Recording` with an ID."""

        metadata_file_path = _create_metadata_file_path(1)
        recording = Recording(metadata_file_path)

        self._check_constant_attributes(recording)
        self.assertEqual(recording.metadata_file_path, metadata_file_path)
        self.assertEqual(recording.id, _EXPECTED_ID)


def _create_metadata_file_path(num):
    file_name = f'Recording {num}.json'
    return _DATA_DIR_PATH / file_name
