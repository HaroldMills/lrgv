import json
import logging

import requests

from lrgv.archiver.archiver_error import ArchiverError
from lrgv.dataflow import SimpleSink


_logger = logging.getLogger(__name__)


# Format for Vesper server login URL. We set the URL to redirect to
# "/health-check/" after login instead of the default "/" since "/"
# redirects to the clip calendar, which is relatively expensive to
# serve.
_LOGIN_URL_SUFFIX_FORMAT = '{}login/?next={}health-check/'

_CREATE_OBJECTS_URL_SUFFIX = 'import-recordings-and-clips/'


class VesperRecordingCreator(SimpleSink):


    def __init__(self, settings, parent=None, name=None):

        super().__init__(settings, parent, name)

        s = settings.vesper

        self._login_url = \
            _LOGIN_URL_SUFFIX_FORMAT.format(s.archive_url, s.archive_url_base)
        self._create_objects_url = s.archive_url + _CREATE_OBJECTS_URL_SUFFIX

        self._username = s.username
        self._password = s.password
        self._session = None


    def _process_item(self, recording, finished):

        if self._session is None:
            self._start_new_session()

        # Create recording in Vesper archive. The recording receives an
        # ID on the server, which is also set as `recording.id`.
        self._create_recording(recording)

        _logger.info(
            f'Processor "{self.path}" created Vesper recording '
            f'{recording.id} for station "{recording.station_name}" '
            f'and start time {recording.start_time}.')

    # TODO: Learn more about HTTP sessions, Django authentication,
    # and the relationship between the two.
    def _start_new_session(self):

        if self._session is not None:
            self._session.close()

        self._session = requests.session()

        try:
            self._get_csrf_token()
        except Exception:
            self._session = None
            raise

        self._log_in()


    def _get_csrf_token(self):

        # Send GET request to Vesper server login page so HTTP session
        # will have Django CSRF token. The token is required for
        # subsequent POST requests that log in to the Vesper server and
        # create clips.
        try:
            response = self._session.get(self._login_url)
        except Exception as e:
            raise ArchiverError(
                f'Could not get CSRF token from Vesper server. HTTP GET '
                f'request raised exception with message: {e}')

        if not response.ok:
            raise ArchiverError(
                f'Could not get CSRF token from Vesper server. HTTP GET '
                f'request returned status code {response.status_code}')


    def _log_in(self):

        data = {
            'username': self._username,
            'password': self._password
        }

        response = _post(self._session, self._login_url, data=data)

        if not response.ok:
            raise ArchiverError('Could not log in to Vesper server.')
        

    def _create_recording(self, recording):

        metadata = recording.metadata_file_contents

        response = \
            _post(self._session, self._create_objects_url, json=metadata)

        if response.status_code == 401:
            # not logged in

            # TODO: Do we need to start a new session here, or just log in?
            # When, exactly, do we need to start a new session? How do we
            # detect when we need to start a new session? Is it just when
            # we find that we are no longer logged in, or is there a more
            # direct way for a client to tell when a session has expired?
            self._start_new_session()
            response = \
                _post(self._session, self._create_objects_url, json=metadata)

        if not response.ok:
            message = response.content.decode(response.encoding)
            raise ArchiverError(
                f'Could not create recording in Vesper archive database. '
                f'Vesper server error message was: {message}')
        
        # If we get here, we sucessfully added the recording to the
        # Vesper archive database. It remains to move the recording
        # metadata file from its existing location to the archived
        # recording directory, adding the recording's Vesper archive
        # ID to its metadata.

        # Set new Vesper recording ID on recording object and in metadata.
        response_data = json.loads(response.content)
        recording_id = response_data['recordings'][0]['id']
        metadata['recordings'][0]['id'] = recording_id

        # Create archived recording directory if needed.
        archived_recording_dir_path = \
            self._settings.archived_recording_dir_path
        try:
            archived_recording_dir_path.mkdir(
                mode=0o755, parents=True, exist_ok=True)
        except Exception as e:
            raise ArchiverError(
                f'Could not create directory '
                f'"{archived_recording_dir_path}". Error message was: {e}')

        # Create new metadata file in archived recording directory.
        old_path = recording.metadata_file_path
        new_path = archived_recording_dir_path / old_path.name
        try:
            with open(new_path, 'wt') as file:
                json.dump(metadata, file, indent=4)
        except Exception as e:
            raise ArchiverError(
                f'Could not create recording metadata file "{new_path}". '
                f'Error message was: {e}')
        
        # Remove old metadata file.
        try:
            old_path.unlink()
        except Exception as e:
            raise ArchiverError(
                f'Could not delete recording metadata file "{old_path}". '
                f'Error message was: {e}')


def _post(session, url, **kwargs):
    headers = _get_post_headers(session)
    return session.post(url, headers=headers, **kwargs)


def _get_post_headers(session):
    return {'X-CSRFToken': session.cookies['csrftoken']}
