class Clip:


    def __init__(self, audio_file_path):
        self._audio_file_path = audio_file_path
        self._metadata_file_path = audio_file_path.with_suffix('.json')


    @property
    def audio_file_path(self):
        return self._audio_file_path
    

    @property
    def metadata_file_path(self):
        return self._metadata_file_path
