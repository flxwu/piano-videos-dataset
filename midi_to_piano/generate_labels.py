import os
import pickle
import numpy as np
import pretty_midi


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


def generate_labels(
    original_midi_name: str,
    new_midi: pretty_midi.PrettyMIDI,
    fps: int = 25,
) -> dict[int, np.ndarray]:
    """
    Generates labels for the given MIDI file
    """
    binary_roll = midi_to_binary_roll(new_midi, frames_per_second=fps)

    dest_frames_dir = "/home/stud/gruener/repos/Audeo/data_hq/input_images/testing"
    dest_labels_dir = "/home/stud/gruener/repos/Audeo/data_hq/labels/testing"
    dest_midi_dir = "/home/stud/gruener/repos/Audeo/data_hq/midi/testing"

    # Keep original video name
    new_video_name = f"video_{original_midi_name}"
    new_video_path = os.path.join(dest_frames_dir, new_video_name)
    new_midi_path = os.path.join(dest_midi_dir, new_video_name)
    os.makedirs(new_video_path, exist_ok=True)
    os.makedirs(new_midi_path, exist_ok=True)

    # Convert binary roll to dictionary format
    label_dict = {}
    for i, roll in enumerate(binary_roll):
        label_dict[i] = roll

    # Save labels in pickle format
    with open(os.path.join(dest_labels_dir, f"{original_midi_name}.pkl"), "wb") as f:
        pickle.dump(label_dict, f)

    # Process MIDI files - create NPZ files for every 50 frames
    for i in range(0, len(binary_roll), 50):
        if i + 50 <= len(binary_roll):
            # Create a 50x88 array for the MIDI data
            midi_data = np.zeros((50, 88), dtype=np.float64)
            # Fill with the corresponding labels
            for j in range(50):
                if i + j < len(binary_roll):
                    midi_data[j] = binary_roll[i + j]

            # Save as NPZ file
            npz_filename = f"{i}-{i + 50}.npz"
            np.savez(os.path.join(new_midi_path, npz_filename), midi=midi_data)

    return label_dict
