import mido
from pathlib import Path

MIDI_PATH = Path(
    r"/Users/felix/My Drive (david10608@gmail.com)/HiWi/bach-2.mid"
).expanduser()

midi_file = mido.MidiFile(MIDI_PATH)

events = []
abs_time = 0
for msg in mido.MidiFile(MIDI_PATH):
    abs_time += msg.time
    events.append((abs_time, msg))

for event in events:
    print(event)
