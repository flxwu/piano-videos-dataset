import mido  # type: ignore
from pathlib import Path

# MIDI_PATH = Path(
#     __file__
# ).parent / "bach-1.mid"
MIDI_PATH = Path(__file__).parent / "midi_to_piano/temp_render/synthesized_bach-1.mid"

midi_file = mido.MidiFile(MIDI_PATH)

events = []
abs_time = 0
for msg in midi_file:
    abs_time += msg.time
    events.append((abs_time, msg))

for event in events:
    print(event)
