"""
Class for synthesizing a new MIDI from a list of NoteEvents.
"""

import pretty_midi  # type: ignore
from midi_to_piano.note_event import NoteEvent


class AnimationResult:
    """
    Class for synthesizing a new MIDI from a list of NoteEvents.
    """

    def __init__(
        self, end_frame: int, fps: int, events_for_note: dict[int, list[NoteEvent]]
    ):
        self.end_frame = end_frame
        self.fps = fps
        self.events_for_note = events_for_note

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
