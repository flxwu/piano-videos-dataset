"""
Class for representing a note event.
"""

import mido  # type: ignore


class NoteEvent:
    """
    Class for representing a note event.
    """

    def __init__(self, msg: mido.Message, on: bool, frame: int):
        self.msg = msg
        self.on = on
        self.frame = frame
