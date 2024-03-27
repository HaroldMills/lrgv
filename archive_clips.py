import logging
import time

from old_bird_clip_mover import OldBirdClipMover
import logging_utils


_logger = logging.getLogger()


def main():

    logging_utils.configure_logging()

    old_bird_clip_mover = create_old_bird_clip_mover()

    while True:

        _logger.info('Moving Old Bird clip files...')
        old_bird_clip_mover.process()

        time.sleep(5)


def create_old_bird_clip_mover():

        name = f'Old Bird Clip Mover'
        mover = OldBirdClipMover(name)

        mover.connect()
        mover.start()

        return mover


if __name__ == '__main__':
    main()
