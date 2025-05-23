import copy
import mido  # type: ignore
from pathlib import Path

MIDI_PATH = Path(
    r"/Users/felix/My Drive (david10608@gmail.com)/HiWi/bach-2.mid"
).expanduser()

mid = mido.MidiFile(MIDI_PATH, clip=True)

new_mid = mido.MidiFile(ticks_per_beat=mid.ticks_per_beat)
