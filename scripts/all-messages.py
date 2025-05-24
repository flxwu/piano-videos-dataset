import mido  # type: ignore
from pathlib import Path

# MIDI_PATH = Path(
#     __file__
# ).parent / "bach-1.mid"
# MIDI_PATH = Path(__file__).parent / "midi_to_piano/temp_render/synthesized_bach-1.mid"

PIANO_KEYS = [
    "A0", "A#0", "B0",
    "C1", "C#1", "D1", "D#1", "E1", "F1", "F#1", "G1", "G#1", "A1", "A#1", "B1",
    "C2", "C#2", "D2", "D#2", "E2", "F2", "F#2", "G2", "G#2", "A2", "A#2", "B2",
    "C3", "C#3", "D3", "D#3", "E3", "F3", "F#3", "G3", "G#3", "A3", "A#3", "B3",
    "C4", "C#4", "D4", "D#4", "E4", "F4", "F#4", "G4", "G#4", "A4", "A#4", "B4",
    "C5", "C#5", "D5", "D#5", "E5", "F5", "F#5", "G5", "G#5", "A5", "A#5", "B5",
    "C6", "C#6", "D6", "D#6", "E6", "F6", "F#6", "G6", "G#6", "A6", "A#6", "B6",
    "C7", "C#7", "D7", "D#7", "E7", "F7", "F#7", "G7", "G#7", "A7", "A#7", "B7",
    "C8"
]  # fmt: skip

MIDI_PATH = Path(
    "/home/wiss/koepa/code/piano-videos-dataset/data/maestro-v3.0.0/2008/MIDI-Unprocessed_01_R1_2008_01-04_ORIG_MID--AUDIO_01_R1_2008_wav--1.midi"
)

midi_file = mido.MidiFile(MIDI_PATH)

events = []
abs_time = 0
for msg in midi_file:
    abs_time += msg.time
    if msg.type in {"note_on", "note_off"}:
        events.append((abs_time, msg))

for event in events:
    if event[1].type == "note_on" and event[1].velocity > 0:
        print(f"{PIANO_KEYS[event[1].note - 21]} ({event[1].note}) on at {event[0]}")
    else:
        print(f"{PIANO_KEYS[event[1].note - 21]} ({event[1].note}) off at {event[0]}")
