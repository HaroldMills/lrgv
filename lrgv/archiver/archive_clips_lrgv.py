import logging
import time

from lrgv.archiver.app_settings_lrgv import app_settings
from lrgv.archiver.clip_audio_file_copier import ClipAudioFileCopier
from lrgv.archiver.clip_audio_file_s3_uploader import ClipAudioFileS3Uploader
from lrgv.archiver.clip_lister import ClipLister
from lrgv.archiver.clip_mover import ClipMover
from lrgv.archiver.detector_clip_deleter import DetectorClipDeleter
from lrgv.archiver.old_bird_clip_converter import OldBirdClipConverter
from lrgv.archiver.old_bird_clip_deleter import OldBirdClipDeleter
from lrgv.archiver.vesper_clip_creator import VesperClipCreator
from lrgv.dataflow import Graph, LinearGraph
from lrgv.util.bunch import Bunch
import lrgv.util.logging_utils as logging_utils


logger = logging.getLogger(__name__)


# To test the LRGV archiver:
#
# 1. Uncomment `_MODE = 'Test'` in `app_settings_lrgv.py` and comment out
#    `_MODE = 'Production'`.
#
# 2. Edit `archive_clips_lrgv.StationClipArchiver._create_processors`
#    according to how you want to process clips.
#
# 3. Open a terminal and cd to
#    "/Users/harold/Desktop/NFC/Data/Old Bird/LRGV/2025/Archiver Test Data/Test Archive".
#
# 4. Initialize and serve the test archive with:
#
#        ./init_and_serve_test_archive.bash
#
# 5. Run `simulate_detection_lrgv.py`.
#
# 6. Run `archive_clips_lrgv.py`.


# TODO: Change the name of the `lrgv` package to something more
#       generic. The package is now used not only by the LRGV project,
#       but also by the Lighthouse project, and might be used by
#       other projects in the future.

# TODO: Consider creating a single `archive_clips` script that could
#       be used for LRGV, Lighthouse, and other projects. The script
#       would ideally be configured by a YAML settings file that would
#       specify all project-specific settings.

# TODO: A Dick-r clip that starts at or after the end of the recording
#       period for a night (e.g. 10:00:00 UTC) causes the Dick clip
#       archiver get stuck on that clip, repeatedly attempting to
#       create the clip in the archive but failing. Implement some
#       remedy for this. Perhaps we should log a warning and move the
#       files for the clip to an Outside directory.

# TODO: Don't attempt to process clip for which audio and metadata files
#       are not both present.

# TODO: Don't stop processing clips for a station and detector if the
#       processing of one clip raises an exception: just move on to the
#       next clip. This will require modifications to dataflow package.

# TODO: Log per-clip messages from station/detector processors.
#       This will require modifications to dataflow package.

# TODO: We currently create clips in the archive for lots of clips from
#       a station and then upload their audio files to S3. Interleave
#       clip creation and audio file uploading so audio is visible in
#       a clip album sooner.

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

        # Archive clips that appear in detectors' `Incoming` clip directories.
        detector_clip_archivers = tuple(
            self._create_detector_clip_archiver(n)
            for n in app_settings.detector_names)

        # Delete clips that appear in detectors' `Incoming` clip directories
        # without archiving them.
        # detector_clip_deleters = tuple(
        #     self._create_detector_clip_deleter(n)
        #     for n in app_settings.detector_names)
        
        # Move clips that appear in detectors' `Archived` clip directories
        # to the detectors' `Retired` clip directories. The `Retired`
        # directories are not SugarSync directories, so after clips are
        # moved there SugarSync no longer has to worry about sychronizing
        # them.
        detector_clip_retirers = tuple(
            self._create_detector_clip_retirer(n)
            for n in app_settings.detector_names)

        processors = (*detector_clip_archivers, *detector_clip_retirers)

        if app_settings.process_old_bird_clips:

            if app_settings.delete_old_bird_clips:

                # Delete Old Bird Dickcissel detector clips that appear in
                # a station's SugarSync directory without archiving them.
                processor = self._create_old_bird_clip_deleter()

            else:

                # Move Old Bird Dickcissel detector clips that appear in
                # a station's SugarSync directory to the detector's
                # `Incoming` clip directory, and add an accompanying
                # clip metadata file.
                processor = self._create_old_bird_clip_converter()

            processors = (processor, *processors)
    
        return processors
    

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


    def _create_detector_clip_deleter(self, detector_name):
            
            s = app_settings
            station_name = self.settings.station_name
            station_paths = s.paths.stations[station_name]
            detector_paths = station_paths.detectors[detector_name]

            settings = Bunch(
                source_clip_dir_path=detector_paths.incoming_clip_dir_path,
                clip_file_wait_period=s.clip_file_wait_period)
                
            return DetectorClipDeleter(settings, self)
        

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
            recorder_name, mic_output_name = \
                s.old_bird_clip_device_data[station_name]
            station_paths = s.paths.stations[station_name]

            settings = Bunch(
                station_name=station_name,
                recorder_name=recorder_name,
                mic_output_name=mic_output_name,
                station_time_zone=s.station_time_zone,
                source_clip_dir_path=station_paths.station_dir_path,
                clip_file_wait_period=s.clip_file_wait_period,
                station_paths=station_paths,
                clip_classification=None)
                
            return OldBirdClipConverter(settings, self)
        

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
