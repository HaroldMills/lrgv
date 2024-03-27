from app_settings import app_settings
from dataflow import Graph, LinearGraph
from file_lister import FileLister
from file_mover import FileMover
from vesper.util.bunch import Bunch


class _OldBirdStationClipMover(LinearGraph):


    type_name = 'Old Bird Station Clip Mover'


    def _create_processors(self):

        s = self.settings

        name = f'{s.station_name} Old Bird Clip Mover - File Lister'
        settings = Bunch(
            dir_path=s.source_dir_path,
            file_name_re=s.clip_file_name_re,
            file_wait_period=s.clip_file_wait_period)
        source = FileLister(name, settings)

        name = f'{s.station_name} Old Bird Clip Mover - File Mover'
        settings = Bunch(destination_dir_path=s.destination_dir_path)
        mover = FileMover(name, settings)

        return source, mover
    

class OldBirdClipMover(Graph):


    type_name = 'Old Bird Clip Mover'


    def _create_processors(self):


        def create_station_clip_mover(station_name):

            name = f'{station_name} Old Bird Clip Mover'

            s = app_settings

            station_paths = s.paths.stations[station_name]
            source_dir_path = station_paths.old_bird_clip_dir_path

            detector_paths = station_paths.detectors[s.old_bird_detector_name]
            destination_dir_path = detector_paths.incoming_clip_dir_path

            settings = Bunch(
                station_name=station_name,
                source_dir_path=source_dir_path,
                clip_file_name_re=s.old_bird_clip_file_name_re,
                clip_file_wait_period=s.clip_file_wait_period,
                destination_dir_path=destination_dir_path)
            
            return _OldBirdStationClipMover(name, settings)
        

        station_names = app_settings.station_names
        return tuple(create_station_clip_mover(n) for n in station_names)
