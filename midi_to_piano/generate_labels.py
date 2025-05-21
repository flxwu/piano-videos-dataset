"""
Generate labels for a MIDI file.
"""

import numpy as np
import pretty_midi  # type: ignore


def midi_to_binary_roll(
    midi: pretty_midi.PrettyMIDI, frames_per_second: int = 25
) -> np.ndarray:
    """
    Converts a MIDI file into a binary piano roll representation.
    """
    # Get the piano roll with the specified resolution
    piano_roll = midi.get_piano_roll(fs=frames_per_second)[0:88, :]
    piano_roll = piano_roll.T

    # shift every press index by -21
    piano_roll = np.roll(piano_roll, -21)
    return piano_roll
