import json
import wave


_METADATA_FILE_NAME_EXTENSION = '.json'


class Clip:


    def __init__(self, audio_file_path, station_name, start_time):

        self._audio_file_path = audio_file_path
        self._station_name = station_name
        self._start_time = start_time

        self._sample_rate = None
        self._length = None
        self._audio_file_contents = None
        self._metadata = None


    @property
    def audio_file_path(self):
        return self._audio_file_path
    

    @property
    def station_name(self):
        return self._station_name
    

    @property
    def start_time(self):
        return self._start_time
    

    @property
    def sample_rate(self):

        # Get sample rate from WAVE file if needed.
        if self._sample_rate is None:
            self._get_audio_file_info()

        return self._sample_rate
    

    def _get_audio_file_info(self):
        with wave.open(str(self.audio_file_path), 'rb') as reader:
            self._length = reader.getnframes()
            self._sample_rate = reader.getframerate()


    @property
    def length(self):

        # Get length from WAVE file if needed.
        if self._length is None:
            self._get_audio_file_info()

        return self._length
    

    @property
    def audio_file_contents(self):

        if self._audio_file_contents is None:
            with open(self.audio_file_path, 'rb') as file:
                self._audio_file_contents = file.read()

        return self._audio_file_contents
        
        
    @property
    def metadata_file_path(self):
        return self.audio_file_path.with_suffix(_METADATA_FILE_NAME_EXTENSION)


    @property
    def metadata(self):
        
        if self._metadata is None:
            with open(self.metadata_file_path, newline='') as file:
                self._metadata = json.load(file)

        return self._metadata
    

    @property
    def classification(self):
        try:
            return self.metadata['clips'][0]['annotations']['Classification']
        except Exception:
            return None
