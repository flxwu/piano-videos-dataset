import copy
import mido
from pathlib import Path

MIDI_PATH = Path(
    r"/Users/felix/My Drive (david10608@gmail.com)/HiWi/bach-2.mid"
).expanduser()

midi_file = mido.MidiFile(MIDI_PATH, clip=True)

new_midi_file = copy.deepcopy(midi_file)
