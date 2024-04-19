import logging
import time

from lrgv.archiver.app_settings import app_settings
from lrgv.archiver.clip_audio_file_copier import ClipAudioFileCopier
from lrgv.archiver.clip_lister import ClipLister
from lrgv.archiver.clip_mover import ClipMover
from lrgv.archiver.old_bird_clip_converter import OldBirdClipConverter
from lrgv.archiver.vesper_clip_creator import VesperClipCreator
from lrgv.dataflow import Graph, LinearGraph
from lrgv.util.bunch import Bunch
import lrgv.util.logging_utils as logging_utils


logger = logging.getLogger(__name__)


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
#       DetectorClipCreator
#           For each clip audio file in "Incoming" clip folder:
#               * Create clip in archive database
#               * Move clip audio file to "Created" clip folder, renaming
#                 according to clip ID.
#               * Delete clip metadata file from "Incoming" clip folder.
#
#       DetectorClipUploader
#           For each clip audio file in "Created" clip folder:
#               * Upload file to S3.
#               * Delete file from "Created" clip folder.
#
#       OldBirdClipConverter
#           For each clip audio file in Old Bird clip folder:
#               * Get clip start time.
#               * Move clip audio file to "Incoming" clip folder, renaming
#                 according to station and start time.
#               * Create clip metadata file in "Incoming" clip folder.


def main():

    s = app_settings
    logging_utils.configure_logging(s.logging_level, s.paths.log_file_path)

    archiver = create_archiver()

    while True:
        logger.info('Looking for new clips to archive...')
        archiver.process()
        time.sleep(5)


def create_archiver():
    archiver = ClipArchiver('Clip Archiver')
    archiver.connect()
    archiver.start()
    return archiver


class ClipArchiver(Graph):
     

    def _create_processors(self):
        return tuple(
            self._create_station_clip_archiver(n)
            for n in app_settings.station_names)
    

    def _create_station_clip_archiver(self, station_name):
        name = f'{station_name} Station Clip Archiver'
        settings = Bunch(station_name=station_name)
        return StationClipArchiver(name, settings)


class StationClipArchiver(Graph):
     

    def _create_processors(self):

        old_bird_clip_converter = self._create_old_bird_clip_converter()

        detector_clip_archivers = tuple(
            self._create_detector_clip_archiver(n)
            for n in app_settings.detector_names)

        return (old_bird_clip_converter,) + detector_clip_archivers


    def _create_old_bird_clip_converter(self):
        
        station_name = self.settings.station_name

        name = f'{station_name} Old Bird Clip Converter'

        s = app_settings
        station_paths = s.paths.stations[station_name]

        settings = Bunch(
            station_name=station_name,
            clip_dir_path=station_paths.station_dir_path,
            clip_file_wait_period=s.clip_file_wait_period,
            station_paths=station_paths)
            
        return OldBirdClipConverter(name, settings)
    

    def _create_detector_clip_archiver(self, detector_name):

        station_name = self.settings.station_name

        name = f'{station_name} {detector_name} Clip Archiver'

        s = app_settings
        station_paths = s.paths.stations[station_name]
        detector_paths = station_paths.detectors[detector_name]

        settings = Bunch(
            detector_paths=detector_paths,
            clip_file_wait_period=s.clip_file_wait_period,
            vesper=s.vesper)
        
        return DetectorClipArchiver(name, settings)


class DetectorClipArchiver(Graph):


    def _create_processors(self):

        s = self.settings

        name = f'{self.name} - Detector Vesper Clip Creator'
        vesper_clip_creator = DetectorVesperClipCreator(name, s)

        name = f'{self.name} - Detector Clip Audio File Copier'
        settings = Bunch(
            detector_paths=s.detector_paths,
            clip_file_wait_period=s.clip_file_wait_period,
            archive_dir_path=app_settings.paths.archive_dir_path)
        audio_file_copier = DetectorClipAudioFileCopier(name, settings)

        return vesper_clip_creator, audio_file_copier

    
    def _process(self, input_data):

        # If any of our subprocessors raises an exception for a clip,
        # we catch it here and log an error message. This keeps the
        # exception from interfering with the processing of subsequent
        # clips.

        try:
            return super()._process(input_data)
        except Exception as e:
            logger.warning(
                f'Detector clip archiver "{self.name}" raised exception. '
                f'Message was: {e}')


class DetectorVesperClipCreator(LinearGraph):


    def _create_processors(self):

        s = self.settings

        name = f'{self.name} - Clip Lister'
        settings = Bunch(
            clip_dir_path=s.detector_paths.incoming_clip_dir_path,
            clip_file_wait_period=s.clip_file_wait_period)
        clip_lister = ClipLister(name, settings)

        name = f'{self.name} - Vesper Clip Creator'
        settings = Bunch(
            vesper=s.vesper,
            created_clip_dir_path=s.detector_paths.created_clip_dir_path)
        clip_creator = VesperClipCreator(name, settings)

        return clip_lister, clip_creator


class DetectorClipAudioFileCopier(LinearGraph):


    def _create_processors(self):

        s = self.settings

        name = f'{self.name} - Clip Lister'
        settings = Bunch(
            clip_dir_path=s.detector_paths.created_clip_dir_path,
            clip_file_wait_period=s.clip_file_wait_period)
        clip_lister = ClipLister(name, settings)

        name = f'{self.name} - Clip Audio File Copier'
        settings = Bunch(archive_dir_path=s.archive_dir_path)
        audio_file_copier = ClipAudioFileCopier(name, settings)

        name = f'{self.name} - Clip Mover'
        settings = Bunch(
            destination_dir_path=s.detector_paths.archived_clip_dir_path)
        clip_mover = ClipMover(name, settings)

        return clip_lister, audio_file_copier, clip_mover
            

if __name__ == '__main__':
    main()
