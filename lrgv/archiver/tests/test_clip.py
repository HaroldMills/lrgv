from pathlib import Path

from lrgv.archiver.clip import Clip
from lrgv.util.test_case import TestCase


_DATA_DIR_PATH = Path(__file__).parent / 'data'
_EXPECTED_ID = 28180
_EXPECTED_STATION_NAME = 'Alamo'
_EXPECTED_MIC_OUTPUT_NAME = '21c 0 Vesper Output'
_EXPECTED_SERIAL_NUM = 2
_EXPECTED_LENGTH = 30870
_EXPECTED_CLASSIFICATION = 'Call.DICK'


class ClipTests(TestCase):
    
    
    def test_initialization_0(self):

        """
        Tests initialization of a `Clip` with no ID, serial number, or
        classification.
        """

        metadata_file_path = _create_metadata_file_path(0)
        clip = Clip(metadata_file_path)

        self.assertEqual(clip.metadata_file_path, metadata_file_path)
        self.assertIsNone(clip.id)
        self.assertEqual(clip.station_name, _EXPECTED_STATION_NAME)
        self.assertIsNone(clip.serial_num)
        self.assertEqual(clip.length, _EXPECTED_LENGTH)
        self.assertIsNone(clip.classification)

        audio_file_path = clip.metadata_file_path.with_suffix('.wav')
        self.assertEqual(clip.audio_file_path, audio_file_path)


    def test_initialization_1(self):

        """
        Tests initialization of a `Clip` with ID, serial number, and
        classification.
        """

        metadata_file_path = _create_metadata_file_path(1)
        clip = Clip(metadata_file_path)

        self.assertEqual(clip.metadata_file_path, metadata_file_path)
        self.assertEqual(clip.id, _EXPECTED_ID)
        self.assertEqual(clip.station_name, _EXPECTED_STATION_NAME)
        self.assertEqual(clip.serial_num, _EXPECTED_SERIAL_NUM)
        self.assertEqual(clip.length, _EXPECTED_LENGTH)
        self.assertEqual(clip.classification, _EXPECTED_CLASSIFICATION)

        audio_file_path = clip.metadata_file_path.with_suffix('.wav')
        self.assertEqual(clip.audio_file_path, audio_file_path)


def _create_metadata_file_path(num):
    file_name = f'Clip {num}.json'
    return _DATA_DIR_PATH / file_name
