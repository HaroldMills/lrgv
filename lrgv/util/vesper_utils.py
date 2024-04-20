from pathlib import Path


def get_clip_audio_file_path(clip_id):

    # Clip file paths have the form "123/456/Clip 123 456 789.wav",
    # where in the example the Vesper archive clip ID is 123456789.

    text = f'{clip_id:09d}'
    p2 = text[0:3]
    p1 = text[3:6]
    p0 = text[6:9]
    return Path(f'{p2}/{p1}/Clip {p2} {p1} {p0}.wav')
