import logging
import time

from lrgv.archiver.app_settings import app_settings
from lrgv.archiver.clip_audio_file_copier import ClipAudioFileCopier
from lrgv.archiver.clip_audio_file_s3_uploader import ClipAudioFileS3Uploader
from lrgv.archiver.clip_lister import ClipLister
from lrgv.archiver.clip_mover import ClipMover
from lrgv.archiver.old_bird_clip_converter import OldBirdClipConverter
from lrgv.archiver.old_bird_clip_deleter import OldBirdClipDeleter
from lrgv.archiver.vesper_clip_creator import VesperClipCreator
from lrgv.dataflow import Graph, LinearGraph
from lrgv.util.bunch import Bunch
import lrgv.util.logging_utils as logging_utils


logger = logging.getLogger(__name__)


# To test the archiver:
#
# 1. Uncomment `_MODE = 'Test'` in `app_settings.py` and comment out
#    `_MODE = 'Production'`.
#
# 2. Edit `archive_clips.StationClipArchiver._create_processors` according
#    to how you want to process Old Bird detector clips.
#
# 3. Open a terminal and cd to
#    "/Users/haroldDesktop/NFC/LRGV/2024/Test Archive".
#
# 4. Initialize and server the test archive with:
#
#        ./init_and_server_test_archive.bash
#
# 5. Run `simulate_detection.py`.
#
# 6. Run `archive_clips.py`.


# TODO: Create an app setting that controls whether or not we archive
#       Old Bird detector clips.

# TODO: A Dick-r clip that starts at or after the end of the recording
#       period for a night (e.g. 10:00:00 UTC) causes the Dick Clip
#       Archiver to try to create a duplicate recording. Decide what
#       should happen and implement. Perhaps we should log a warning
#       and move the clip files to an Outside directory.

# TODO: Don't attempt to process clip for which audio and metadata files
#       are not both present.

# TODO: Consider uploading clip audio file *before* adding clip to archive
#       so users don't see blank spectrograms in clip albums.

# TODO: Don't stop processing clips for a station and detector if the
#       processing of one clip raises an exception: just move on to the
#       next clip. This will require modifications to dataflow package.

# TODO: Log per-clip messages from station/detector processors.
#       This will require modifications to dataflow package.


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


'''
LRGV
    Alamo
        OldBirdClipConverter
        Dick
            DetectorVesperClipCreator
                ClipLister
                    FileLister
                    ClipObjectCreator
                VesperClipCreator
            DetectorClipAudioFileS3Uploader
                ClipLister
                    FileLister
                    ClipObjectCreator
                DetectorClipAudioFileCopier
                    ClipLister
                        FileLister
                        ClipObjectCreator
                    ClipAudioFileCopier
                    ClipMover
'''


def main():

    s = app_settings
    logging_utils.configure_logging(s.logging_level, s.paths.log_file_path)

    archiver = create_archiver()

    while True:
        logger.info('Looking for new clips to archive...')
        archiver.process()
        time.sleep(5)


def create_archiver():
    archiver = ClipArchiver(name='LRGV')
    archiver.connect()
    archiver.start()
    return archiver


class ClipArchiver(Graph):
     

    def _create_processors(self):
        return tuple(
            self._create_station_clip_archiver(n)
            for n in app_settings.station_names)
    

    def _create_station_clip_archiver(self, station_name):
        settings = Bunch(station_name=station_name)
        return StationClipArchiver(settings, self, station_name)


class StationClipArchiver(Graph):
     

    def _create_processors(self):

        # old_bird_clip_converter = self._create_old_bird_clip_converter()

        old_bird_clip_deleter = self._create_old_bird_clip_deleter()

        detector_clip_archivers = tuple(
            self._create_detector_clip_archiver(n)
            for n in app_settings.detector_names)
        
        detector_clip_retirers = tuple(
            self._create_detector_clip_retirer(n)
            for n in app_settings.detector_names)

        # return \
        #     (old_bird_clip_converter,) + detector_clip_archivers + \
        #     detector_clip_retirers
        return \
            (old_bird_clip_deleter,) + detector_clip_archivers + \
            detector_clip_retirers
        # return detector_clip_archivers + detector_clip_retirers
    

    def _create_old_bird_clip_deleter(self):
            
            s = app_settings
            station_name = self.settings.station_name
            station_paths = s.paths.stations[station_name]

            settings = Bunch(
                source_clip_dir_path=station_paths.station_dir_path,
                clip_file_wait_period=s.clip_file_wait_period)
                
            return OldBirdClipDeleter(settings, self)
        

    def _create_old_bird_clip_converter(self):
            
            s = app_settings
            station_name = self.settings.station_name
            station_paths = s.paths.stations[station_name]

            settings = Bunch(
                station_name=station_name,
                source_clip_dir_path=station_paths.station_dir_path,
                clip_file_wait_period=s.clip_file_wait_period,
                station_paths=station_paths,
                clip_classification=None)
                
            return OldBirdClipConverter(settings, self)
        

    def _create_detector_clip_archiver(self, detector_name):

        s = app_settings
        station_name = self.settings.station_name
        station_paths = s.paths.stations[station_name]
        detector_paths = station_paths.detectors[detector_name]

        settings = Bunch(
            archive_remote=s.archive_remote,
            detector_paths=detector_paths,
            clip_file_wait_period=s.clip_file_wait_period,
            vesper=s.vesper)
        
        if s.archive_remote:
            settings.aws = s.aws
       
        name = f'{detector_name}'

        return DetectorClipArchiver(settings, self, name)


    def _create_detector_clip_retirer(self, detector_name):

        s = app_settings
        station_name = self.settings.station_name
        station_paths = s.paths.stations[station_name]
        detector_paths = station_paths.detectors[detector_name]

        settings = Bunch(
            detector_paths=detector_paths,
            clip_file_wait_period=s.clip_file_retirement_wait_period)
        
        name = f'{detector_name} Clip Retirer'

        return DetectorClipRetirer(settings, self, name)


class DetectorClipArchiver(Graph):


    def _create_processors(self):

        s = self.settings

        vesper_clip_creator = DetectorVesperClipCreator(s, self)

        if s.archive_remote:

            settings = Bunch(
                detector_paths=s.detector_paths,
                clip_file_wait_period=s.clip_file_wait_period,
                aws=s.aws)
            audio_file_handler = \
                DetectorClipAudioFileS3Uploader(settings, self)
            
        else:
            # archive local

            settings = Bunch(
                detector_paths=s.detector_paths,
                clip_file_wait_period=s.clip_file_wait_period,
                archive_dir_path=app_settings.paths.archive_dir_path)
            audio_file_handler = \
                DetectorClipAudioFileCopier(settings, self)

        return vesper_clip_creator, audio_file_handler

    
    def _process(self, input_data):

        # If any of our subprocessors raises an exception for a clip,
        # we catch it here and log an error message. This keeps the
        # exception from interfering with the processing of subsequent
        # clips.

        try:
            return super()._process(input_data)
        except Exception as e:
            logger.warning(
                f'Processor "{self.path}" raised exception. Message '
                f'was: {e}')


class DetectorVesperClipCreator(LinearGraph):


    def _create_processors(self):

        s = self.settings

        settings = Bunch(
            clip_dir_path=s.detector_paths.incoming_clip_dir_path,
            clip_file_wait_period=s.clip_file_wait_period)
        clip_lister = ClipLister(settings, self)

        settings = Bunch(
            vesper=s.vesper,
            created_clip_dir_path=s.detector_paths.created_clip_dir_path)
        clip_creator = VesperClipCreator(settings, self)

        return clip_lister, clip_creator


class DetectorClipAudioFileS3Uploader(LinearGraph):


    def _create_processors(self):

        s = self.settings

        settings = Bunch(
            clip_dir_path=s.detector_paths.created_clip_dir_path,
            clip_file_wait_period=s.clip_file_wait_period)
        clip_lister = ClipLister(settings, self)

        settings = Bunch(aws=s.aws)
        audio_file_uploader = ClipAudioFileS3Uploader(settings, self)

        settings = Bunch(
            destination_dir_path=s.detector_paths.archived_clip_dir_path)
        clip_mover = ClipMover(settings, self)

        return clip_lister, audio_file_uploader, clip_mover
    

class DetectorClipAudioFileCopier(LinearGraph):


    def _create_processors(self):

        s = self.settings

        settings = Bunch(
            clip_dir_path=s.detector_paths.created_clip_dir_path,
            clip_file_wait_period=s.clip_file_wait_period)
        clip_lister = ClipLister(settings, self)

        settings = Bunch(archive_dir_path=s.archive_dir_path)
        audio_file_copier = ClipAudioFileCopier(settings, self)

        settings = Bunch(
            destination_dir_path=s.detector_paths.archived_clip_dir_path)
        clip_mover = ClipMover(settings, self)

        return clip_lister, audio_file_copier, clip_mover
            

class DetectorClipRetirer(LinearGraph):


    def _create_processors(self):
        
        s = self.settings

        settings = Bunch(
            clip_dir_path=s.detector_paths.archived_clip_dir_path,
            clip_file_wait_period=s.clip_file_wait_period)
        clip_lister = ClipLister(settings, self)

        settings = Bunch(
            destination_dir_path=s.detector_paths.retired_clip_dir_path)
        clip_mover = ClipMover(settings, self)

        return clip_lister, clip_mover


if __name__ == '__main__':
    main()
