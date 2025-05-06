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

_CREATE_CLIPS_URL_SUFFIX = 'import-recordings-and-clips/'


class VesperClipCreator(SimpleSink):


    def __init__(self, settings, parent=None, name=None):

        super().__init__(settings, parent, name)

        s = settings.vesper

        self._login_url = \
            _LOGIN_URL_SUFFIX_FORMAT.format(s.archive_url, s.archive_url_base)
        self._create_clips_url = s.archive_url + _CREATE_CLIPS_URL_SUFFIX

        self._username = s.username
        self._password = s.password
        self._session = None


    def _process_item(self, clip, finished):

        if self._session is None:
            self._start_new_session()

        # Create clip in Vesper archive. The clip receives an ID on
        # the server, which is also set as `clip.id`.
        self._create_clip(clip)

        _logger.info(
            f'Processor "{self.path}" created Vesper clip {clip.id} '
            f'for station "{clip.station_name}", start time '
            f'{clip.start_time}.')


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
        

    def _create_clip(self, clip):

        metadata = clip.metadata_file_contents

        response = _post(self._session, self._create_clips_url, json=metadata)

        if response.status_code == 401:
            # not logged in

            # TODO: Do we need to start a new session here, or just log in?
            # When, exactly, do we need to start a new session? How do we
            # detect when we need to start a new session? Is it just when
            # we find that we are no longer logged in, or is there a more
            # direct way for a client to tell when a session has expired?
            self._start_new_session()
            response = \
                _post(self._session, self._create_clips_url, json=metadata)

        if not response.ok:
            message = response.content.decode(response.encoding)
            raise ArchiverError(
                f'Could not create clip in Vesper archive database. '
                f'Vesper server error message was: {message}')
        
        # If we get here, we sucessfully added the new clip to the
        # Vesper archive database. It remains to move the clip files
        # to from their existing location to the created clip
        # directory, adding the clip's Vesper archive ID to its
        # metadata. Unfortunately we can't just move the files with
        # a `ClipMover` processor since it doesn't know how to add
        # the clip ID.

        # Set new Vesper clip ID on clip object and in metadata.
        response_data = json.loads(response.content)
        clip_id = response_data['clips'][0]['id']
        metadata['clips'][0]['id'] = clip_id

        # Move audio file to created clip directory.
        old_path = clip.audio_file_path
        new_path = self._settings.created_clip_dir_path / old_path.name
        try:
            old_path.rename(new_path)
        except Exception as e:
            raise ArchiverError(
                f'Could not move clip audio file "{old_path}" to '
                f'"{new_path.parent}". Error message was: {e}')
        
        # Create new metadata file in created clip directory.
        old_path = clip.metadata_file_path
        new_path = self._settings.created_clip_dir_path / old_path.name
        try:
            with open(new_path, 'wt') as file:
                json.dump(metadata, file, indent=4)
        except Exception as e:
            raise ArchiverError(
                f'Could not create clip metadata file "{new_path}". '
                f'Error message was: {e}')
        
        # Remove old metadata file.
        try:
            old_path.unlink()
        except Exception as e:
            raise ArchiverError(
                f'Could not delete clip metadata file "{old_path}". '
                f'Error message was: {e}')


def _post(session, url, **kwargs):
    headers = _get_post_headers(session)
    return session.post(url, headers=headers, **kwargs)


def _get_post_headers(session):
    return {'X-CSRFToken': session.cookies['csrftoken']}
