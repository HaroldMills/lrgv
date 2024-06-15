"""Processor that uploads a clip audio file to an AWS S3 bucket."""


import boto3

from lrgv.archiver.archiver_error import ArchiverError
from lrgv.dataflow import SimpleProcessor
import lrgv.util.vesper_utils as vesper_utils


class ClipAudioFileS3Uploader(SimpleProcessor):


    def __init__(self, settings, parent=None, name=None):

        super().__init__(settings, parent, name)

        aws = self.settings.aws

        self._clip_bucket_name = aws.s3_clip_bucket_name
        self._clip_folder_path = aws.s3_clip_folder_path

        session = boto3.Session(
            aws_access_key_id=aws.access_key_id,
            aws_secret_access_key=aws.secret_access_key,
            region_name=aws.region_name)
        self._s3 = session.resource('s3')


    def _process_item(self, clip, finished):

        object_key = self._get_clip_object_key(clip.id)
        file_contents = clip.audio_file_contents

        try:
            obj = self._s3.Object(self._clip_bucket_name, object_key)
        except Exception as e:
            raise ArchiverError(
                f'Processor "{self.path}" not create boto3 S3 object for '
                f'bucket "{self._clip_bucket_name}", object key '
                f'"{object_key}". Exception message was: {e}')
        
        try:
            obj.put(Body=file_contents)
        except Exception as e:
            raise ArchiverError(
                f'Processor "{self.path}" could not put boto3 S3 object to '
                f'bucket "{self._clip_bucket_name}", object key '
                f'"{object_key}". Exception message was: {e}')
        
        return clip


    def _get_clip_object_key(self, clip_id):

        # Clip object keys have the form
        # "{clip_folder_path}000/000/Clip 000 000 243.wav". Note that if
        # the clip folder path is not empty it should end with a "/".

        clip_file_path = vesper_utils.get_clip_audio_file_path(clip_id)
        return f'{self._clip_folder_path}' + '/'.join(clip_file_path.parts)
