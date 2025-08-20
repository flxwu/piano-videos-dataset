"""
Class for synthesizing a new MIDI from a list of NoteEvents.
"""

import pretty_midi  # type: ignore
from midi_to_piano.note_event import NoteEvent
import numpy.typing as npt
import numpy as np


class AnimationResult:
    """
    Class for synthesizing a new MIDI from a list of NoteEvents.
    """

    def __init__(
        self, end_frame: int, fps: int, events_for_note: dict[int, list[NoteEvent]]
    ):
        self.end_frame = end_frame  # last frame of the animation, i.e. last frame where a note is pressed
        self.fps = fps
        self.events_for_note = events_for_note

    def get_frames_to_notes_pressed(self) -> dict[int, npt.NDArray[np.int_]]:
        """
        Get the notes pressed at a given frame.
        """
        A0_MIDI = 21  # lowest key on an 88-key piano
        C8_MIDI = 108  # highest key on an 88-key piano
        amount_frames = self.end_frame
        # initialize dict with amount_frames keys and a 88-entry array of 0s
        frames_to_notes_pressed: dict[int, npt.NDArray[np.int_]] = {
            frame: np.zeros(88, dtype=np.int8) for frame in range(amount_frames + 1)
        }
        for note_number in range(A0_MIDI, C8_MIDI + 1):
            events_for_note = self.events_for_note.get(note_number, [])
            # events_for_note is a list of note events.
            # i.e. if key is pressed at frame 10 and released at frame 15,
            # events_for_note will be a list with two elements:
            # (msg, on, 10) and (msg, off, 15)
            # That means we want to set frames_to_notes_pressed[frame][note_number - A0_MIDI] = 1
            # for ALL frames from 10 to 14.
            # We can do this by iterating over all events and setting the value to 1
            # for all frames between the event's frame and the next event's frame.
            i = 0
            while i < len(events_for_note):
                event = events_for_note[i]
                if event.on:
                    next_event = events_for_note[i + 1]
                    # next_event should be off
                    if next_event.on:
                        raise ValueError(
                            f"Next event for note {note_number} is an on event"
                        )
                    # set frames_to_notes_pressed[frame][note_number - A0_MIDI] = 1
                    # for all frames between event.frame and next_event.frame
                    for frame in range(event.frame, next_event.frame):
                        frames_to_notes_pressed[frame][note_number - A0_MIDI] = 1
                        # print(f"[NUMPY LABELS] Adding note {note_number} at frame {frame}")
                i += 1

        # convert to numpy array
        for frame, notes_pressed in frames_to_notes_pressed.items():
            frames_to_notes_pressed[frame] = np.array(notes_pressed, dtype=np.int8)
        return frames_to_notes_pressed

    def synthesize_new_midi(self) -> pretty_midi.PrettyMIDI:
        """
        Synthesize a new MIDI from the class's NoteEvents.
        """
        piano_out = pretty_midi.PrettyMIDI()
        piano_program = pretty_midi.instrument_name_to_program("Acoustic Grand Piano")
        piano = pretty_midi.Instrument(program=piano_program)
        # For each note, collapse the 'on' and 'off' events into a single note
        for note_number, note_events in self.events_for_note.items():
            # note_events is a list of (msg, on, free_frame) tuples
            # if we get (msg, on) followed by (msg, off), we add a note to pretty_midi_notes
            for i, note_event in enumerate(note_events):
                if (
                    note_event.on
                    and i + 1 < len(note_events)
                    and not note_events[i + 1].on
                ):
                    # we have an 'on' event followed by an 'off' event
                    piano.notes.append(
                        pretty_midi.Note(
                            velocity=note_event.msg.velocity,
                            pitch=note_number,
                            start=note_event.frame / self.fps,
                            end=note_events[i + 1].frame / self.fps,
                        )
                    )
        piano_out.instruments.append(piano)
        return piano_out
