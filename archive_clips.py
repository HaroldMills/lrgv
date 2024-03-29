import logging
import time

from app_settings import app_settings
from dataflow import Graph
from old_bird_clip_mover import OldBirdClipMover
from vesper.util.bunch import Bunch
import logging_utils


logger = logging.getLogger()


# RESUME:
#
# * In top level processor, create one processor per station. The processor
#   for a station will include one processor per detector for that station.
#   If we will run the Old Bird Dickcissel detector at the station it will
#   also include a processor that moves clips from the station clip
#   folder to the detector's Incoming folder, renaming them and adding
#   clip metadata files.
#
#       StationClipArchiver
#
#       DetectorClipArchiver
#
#       ArchiveClipCreator
#           For each clip audio file in "Incoming" clip folder:
#               * Create clip in archive database
#               * Move clip audio file to "Created" clip folder, renaming
#                 according to clip ID.
#               * Delete clip metadata file from "Incoming" clip folder.
#
#       ClipAudioFileS3Uploader
#           For each clip audio file in "Created" clip folder:
#               * Upload file to S3.
#               * Delete file from "Created" clip folder.
#
#       OldBirdClipMover
#           For each clip audio file in Old Bird clip folder:
#               * Get clip start time.
#               * Move clip audio file to "Incoming" clip folder, renaming
#                 according to station and start time.
#               * Create clip metadata file in "Incoming" clip folder.


def main():

    logging_utils.configure_logging()

    archiver = create_archiver()

    while True:
        archiver.process()
        time.sleep(5)


def create_archiver():

        name = f'Clip Archiver'
        archiver = ClipArchiver(name)
        
        archiver.connect()
        archiver.start()

        return archiver


class ClipArchiver(Graph):
     

     type_name = 'Clip Archiver'


     def _create_processors(self):
          
          def create_station_clip_archiver(station_name):
               name = f'{station_name} Station Clip Archiver'
               settings = Bunch(station_name=station_name)
               return StationClipArchiver(name, settings)

          return tuple(
               create_station_clip_archiver(n)
               for n in app_settings.station_names)
              
          

class StationClipArchiver(Graph):
     

     type_name = 'Station Clip Archiver'


     def _create_processors(self):
        
        station_name = self.settings.station_name

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
        
        return (OldBirdClipMover(name, settings),)
     

if __name__ == '__main__':
    main()
