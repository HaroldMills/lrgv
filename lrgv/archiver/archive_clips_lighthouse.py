import logging
import time

from lrgv.archiver.app_settings_lighthouse import app_settings
from lrgv.archiver.clip_audio_file_copier import ClipAudioFileCopier
from lrgv.archiver.clip_audio_file_s3_uploader import ClipAudioFileS3Uploader
from lrgv.archiver.clip_lister import ClipLister
from lrgv.archiver.clip_mover import ClipMover
from lrgv.archiver.clip_deleter import ClipDeleter
from lrgv.archiver.old_bird_clip_converter import OldBirdClipConverter
from lrgv.archiver.old_bird_clip_deleter import OldBirdClipDeleter
from lrgv.archiver.recording_lister import RecordingLister
from lrgv.archiver.recording_mover import RecordingMover
from lrgv.archiver.vesper_clip_creator import VesperClipCreator
from lrgv.archiver.vesper_recording_creator import VesperRecordingCreator
from lrgv.dataflow import Graph, LinearGraph
from lrgv.util.bunch import Bunch
import lrgv.util.logging_utils as logging_utils


logger = logging.getLogger(__name__)


# To test the Lighthouse archiver:
#
# 1. Uncomment `_MODE = 'Test'` in `app_settings_lighthouse.py` and comment out
#    `_MODE = 'Production'`.
#
# 2. Edit `archive_clips_lighthouse.StationArchiver._create_processors`
#    according to how you want to process clips.
#
# 3. Open a terminal and cd to
#    "/Users/harold/Desktop/NFC/Data/Old Bird/Lighthouse/2025/Archiver Test Data/Test Archive".
#
# 4. Initialize and serve the test archive with:
#
#        ./init_and_serve_test_archive.bash
#
# 5. Run `simulate_detection_lighthouse.py`.
#
# 6. Run `archive_clips_lighthouse.py`.


'''
Processor hierarchy:

Archiver (e.g. LRGV)
    StationArchiver (e.g. Alamo)
        RecordingArchiver (e.g. Vesper Recorder)
            RecordingMetadataArchiver
                RecordingLister
                VesperRecordingCreator
             RecordingRetirer
                RecordingLister
                RecordingMover
        OldBirdClipConverter
        ClipArchiver (e.g. Dick or Nighthawk)
            ClipMetadataArchiver
                ClipLister
                VesperClipCreator
            ClipAudioFileS3Archiver
                ClipLister
                ClipAudioFileS3Uploader
                ClipMover
            ClipAudioFileLocalArchiver
                ClipLister
                ClipAudioFileCopier
                ClipMover
            ClipRetirer
                ClipLister
                ClipMover
'''


def main():

    s = app_settings
    logging_utils.configure_logging(s.logging_level, s.paths.log_file_path)

    archiver = create_archiver()

    while True:
        logger.info('Looking for new recordings and clips to archive...')
        archiver.process()
        time.sleep(5)


def create_archiver():
    archiver = Archiver(name=app_settings.project_name)
    archiver.connect()
    archiver.start()
    return archiver


class Archiver(Graph):
     

    def _create_processors(self):
        return tuple(
            self._create_station_archiver(n)
            for n in app_settings.station_names)
    

    def _create_station_archiver(self, station_name):
        settings = Bunch(station_name=station_name)
        return StationArchiver(settings, self, station_name)


class StationArchiver(Graph):
     

    def _create_processors(self):

        # Archive recordings that appear in recorders' `Incoming` recording
        # directories.
        recording_archivers = tuple(
            self._create_recording_archiver(n)
            for n in app_settings.recorder_names)
        
        # Archive clips that appear in detectors' `Incoming` clip directories.
        clip_archivers = tuple(
            self._create_clip_archiver(n)
            for n in app_settings.detector_names)

        # Delete clips that appear in detectors' `Incoming` clip directories
        # without archiving them.
        # clip_deleters = tuple(
        #     self._create_clip_deleter(n)
        #     for n in app_settings.detector_names)
        
        processors = (*recording_archivers, *clip_archivers)

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
    

    def _create_recording_archiver(self, recorder_name):

        s = app_settings
        station_name = self.settings.station_name
        station_paths = s.paths.stations[station_name]
        recorder_paths = station_paths.recorders[recorder_name]

        settings = Bunch(
            recorder_paths=recorder_paths,
            recording_file_wait_period=s.recording_file_wait_period,
            recording_file_retirement_wait_period=
                s.recording_file_retirement_wait_period,
            vesper=s.vesper)

        return RecordingArchiver(settings, self, recorder_name)
    

    def _create_clip_archiver(self, detector_name):

        s = app_settings
        station_name = self.settings.station_name
        station_paths = s.paths.stations[station_name]
        detector_paths = station_paths.detectors[detector_name]

        settings = Bunch(
            archive_remote=s.archive_remote,
            detector_paths=detector_paths,
            clip_file_wait_period=s.clip_file_wait_period,
            clip_file_retirement_wait_period=
                s.clip_file_retirement_wait_period,
            vesper=s.vesper)
        
        if s.archive_remote:
            settings.aws = s.aws
       
        name = f'{detector_name}'

        return ClipArchiver(settings, self, name)


    def _create_clip_deleter(self, detector_name):
            
            s = app_settings
            station_name = self.settings.station_name
            station_paths = s.paths.stations[station_name]
            detector_paths = station_paths.detectors[detector_name]

            settings = Bunch(
                source_clip_dir_path=detector_paths.incoming_clip_dir_path,
                clip_file_wait_period=s.clip_file_wait_period)
                
            return ClipDeleter(settings, self)
        

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
        

class RecordingArchiver(Graph):


    def _create_processors(self):
        s = self.settings
        metadata_archiver = RecordingMetadataArchiver(s, self)
        retirer = RecordingRetirer(s, self)
        return metadata_archiver, retirer

    
    def _process(self, input_data):

        # If any of our subprocessors raises an exception for a recording,
        # we catch it here and log an error message. Unfortunately, this
        # doesn't allow us to process subsequent recordings for the same
        # station and recorder, as long as subsequent attempts to process
        # the same recording raise the same exception.

        try:
            return super()._process(input_data)
        except Exception as e:
            logger.warning(
                f'Processor "{self.path}" raised exception. Message '
                f'was: {e}')
            
            
class RecordingMetadataArchiver(LinearGraph):


    def _create_processors(self):

        s = self.settings

        settings = Bunch(
            recording_dir_path=s.recorder_paths.incoming_recording_dir_path,
            recording_file_wait_period=s.recording_file_wait_period)
        recording_lister = RecordingLister(settings, self)

        settings = Bunch(
            vesper=s.vesper,
            archived_recording_dir_path=(
                s.recorder_paths.archived_recording_dir_path))
        recording_creator = VesperRecordingCreator(settings, self)

        return recording_lister, recording_creator
    

class RecordingRetirer(LinearGraph):

    """
    Moves recordings that appear in a detector's `Archived` recording
    directory to the detector's `Retired` recording directory. The
    `Retired` directory is not a SugarSync directory, so after recordings
    are moved there SugarSync no longer has to synchronize them.
    """

    def _create_processors(self):
        
        s = self.settings

        settings = Bunch(
            recording_dir_path=s.recorder_paths.archived_recording_dir_path,
            recording_file_wait_period=s.recording_file_retirement_wait_period)
        recording_lister = RecordingLister(settings, self)

        settings = Bunch(
            destination_dir_path=s.recorder_paths.retired_recording_dir_path)
        recording_mover = RecordingMover(settings, self)

        return recording_lister, recording_mover


class ClipArchiver(Graph):


    def _create_processors(self):

        s = self.settings

        metadata_archiver = ClipMetadataArchiver(s, self)

        if s.archive_remote:

            settings = Bunch(
                detector_paths=s.detector_paths,
                clip_file_wait_period=s.clip_file_wait_period,
                aws=s.aws)
            
            audio_file_archiver = ClipAudioFileS3Archiver(settings, self)
            
        else:
            # archive local

            settings = Bunch(
                detector_paths=s.detector_paths,
                clip_file_wait_period=s.clip_file_wait_period,
                archive_dir_path=app_settings.paths.archive_dir_path)
            
            audio_file_archiver = ClipAudioFileLocalArchiver(settings, self)

        settings = Bunch(
            detector_paths=s.detector_paths,
            clip_file_wait_period=s.clip_file_retirement_wait_period)
        
        retirer = ClipRetirer(settings, self)

        return metadata_archiver, audio_file_archiver, retirer

    
    def _process(self, input_data):

        # If any of our subprocessors raises an exception for a clip,
        # we catch it here and log an error message. Unfortunately, this
        # doesn't allow us to process subsequent clips for the same
        # station and detector, as long as subsequent attempts to process
        # the same clip raise the same exception.

        try:
            return super()._process(input_data)
        except Exception as e:
            logger.warning(
                f'Processor "{self.path}" raised exception. Message '
                f'was: {e}')


class ClipMetadataArchiver(LinearGraph):


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


class ClipAudioFileS3Archiver(LinearGraph):


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
    

class ClipAudioFileLocalArchiver(LinearGraph):


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
            

class ClipRetirer(LinearGraph):

    """
    Moves clips that appear in a detector's `Archived` clip directory
    to the detector's `Retired` clip directory. The `Retired` directory
    is not a SugarSync directory, so after clips are moved there
    SugarSync no longer has to synchronize them.
    """

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
