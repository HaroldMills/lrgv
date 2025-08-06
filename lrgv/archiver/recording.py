"""
Convenience interface for recording data stored in a JSON metadata file.

The metadata file format provides for the description of metadata for
any number of recordings, but this class assumes that each file describes
exactly one recording.
"""


from datetime import datetime as DateTime
import json


class Recording:


    def __init__(self, metadata_file_path):
        self._metadata_file_path = metadata_file_path
        self._metadata_file_contents = None


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
    def _metadata(self):
       return self.metadata_file_contents['recordings'][0]


    @property
    def id(self):

        # Not every recording metadata file includes a clip ID, so we
        # return `None` when it is absent.
        try:
            return self._metadata['id']
        except KeyError:
            return None
            

    @property
    def station_name(self):
        return self._metadata['station']
    

    @property
    def recorder_name(self):
        return self._metadata['recorder']
    

    @property
    def mic_output_names(self):
        return self._metadata['mic_outputs']


    @property
    def start_time(self):

        # Get start time in ISO 8601 format.
        date, time, tz = self._metadata['start_time'].split()
        start_time = f'{date}T{time}{tz}'

        return DateTime.fromisoformat(start_time)


    @property
    def length(self):
        return int(self._metadata['length'])
    

    @property
    def sample_rate(self):
        return int(self._metadata['sample_rate'])
