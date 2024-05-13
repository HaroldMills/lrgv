"""
Convenience interface for clip data stored in a JSON metadata file and
a WAVE audio file.

The metadata file format provides for the description of metadata for
any number of clips, but this class assumes that each file describes
exactly one clip.
"""


from datetime import datetime as DateTime
import json


_AUDIO_FILE_NAME_EXTENSION = '.wav'


class Clip:


    def __init__(self, metadata_file_path):
        self._metadata_file_path = metadata_file_path
        self._metadata_file_contents = None
        self._audio_file_contents = None


    @property
    def metadata_file_path(self):
        return self._metadata_file_path
    

    @property
    def metadata_file_contents(self):

        if self._metadata_file_contents is None:
            with open(self.metadata_file_path, newline='') as file:
                self._metadata_file_contents = json.load(file)

        return self._metadata_file_contents

 
    @property
    def _clip_metadata(self):
       return self.metadata_file_contents['clips'][0]


    @property
    def id(self):

        # Not every clip metadata file includes a clip ID, so we
        # return `None` when it is absent.
        try:
            return self._clip_metadata['id']
        except KeyError:
            return None
            

    @property
    def station_name(self):

        # Extract station name from recording name. The recording
        # name has the form "<station name> <date> <time> Z". We
        # use `rsplit` with a `maxsplit` argument to split it since
        # the station name may contain spaces.
        recording_name = self._clip_metadata['recording']
        return recording_name.rsplit(maxsplit=3)[0]


    @property
    def start_time(self):

        # Get start time in ISO 8601 format.
        date, time, tz = self._clip_metadata['start_time'].split()
        start_time = f'{date}T{time}{tz}'

        return DateTime.fromisoformat(start_time)


    @property
    def serial_num(self):

        # Not every clip metadata file includes a clip serial number,
        # so we return `None` when it is absent.
        try:
            serial_num = self._clip_metadata['serial_num']
        except KeyError:
            return None
        
        return int(serial_num)


    @property
    def sample_rate(self):
        metadata = self._metadata_file_contents
        clip = metadata['clips'][0]
        recording_name = clip['recording']
        recording = metadata['recordings'][recording_name]
        return float(recording['sample_rate'])


    @property
    def length(self):
        return int(self._clip_metadata['length'])
    

    @property
    def classification(self):

        # Not every clip will have a `Classification` annotation, so
        # we return `None` when it is absent.
        try:
            return self._clip_metadata['annotations']['Classification']
        except KeyError:
            return None


    @property
    def audio_file_path(self):
        return self.metadata_file_path.with_suffix(_AUDIO_FILE_NAME_EXTENSION)
    

    @property
    def audio_file_contents(self):

        if self._audio_file_contents is None:
            with open(self.audio_file_path, 'rb') as file:
                self._audio_file_contents = file.read()

        return self._audio_file_contents
