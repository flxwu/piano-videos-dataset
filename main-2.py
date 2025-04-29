import mido
from pathlib import Path

MIDI_PATH = Path(
    r"/Users/felix/My Drive (david10608@gmail.com)/HiWi/bach-2.mid"
).expanduser()

midi_file = mido.MidiFile(MIDI_PATH, clip=True)

# USE MIDO to convert these to a list of note onsets and offsets
tempo = 431655
ticks_per_beat = midi_file.ticks_per_beat
curr_velocity = 0
