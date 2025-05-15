import mido


class NoteEvent:
    def __init__(self, msg: mido.Message, on: bool, frame: int):
        self.msg = msg
        self.on = on
        self.frame = frame

