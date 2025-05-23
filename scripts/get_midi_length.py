#!/usr/bin/env python3

import mido  # type: ignore
import sys
from pathlib import Path


def get_midi_length(midi_path: str) -> float:
    """
    Get the length of a MIDI file in seconds.

    Args:
        midi_path: Path to the MIDI file

    Returns:
        Length of the MIDI file in seconds
    """
    midi_file = mido.MidiFile(midi_path)
    return midi_file.length


def process_path(path_str: str) -> tuple[float, int]:
    """
    Process a path (file or directory) and return total length and file count.

    Args:
        path: Path to a MIDI file or directory containing MIDI files

    Returns:
        Tuple of (total_length, file_count)
    """
    path = Path(path_str)
    total_length = 0.0
    file_count = 0

    if path.is_file():
        if path.suffix.lower() == ".midi":
            try:
                length = get_midi_length(str(path))
                total_length += length
                file_count += 1
                print(f"{path.name}: {length:.2f} seconds")
            except Exception as e:
                print(f"Error reading {path.name}: {e}")
    elif path.is_dir():
        for midi_file in path.glob("**/*.midi"):
            try:
                length = get_midi_length(str(midi_file))
                total_length += length
                file_count += 1
                print(f"{midi_file.name}: {length:.2f} seconds")
            except Exception as e:
                print(f"Error reading {midi_file.name}: {e}")
    else:
        print(f"Error: Path does not exist: {path}")
        sys.exit(1)

    return total_length, file_count


def main():
    if len(sys.argv) != 2:
        print("Usage: python get_midi_length.py <path_to_midi_file_or_folder>")
        sys.exit(1)

    path = sys.argv[1]
    if not Path(path).exists():
        print(f"Error: Path not found: {path}")
        sys.exit(1)

    print("\nProcessing MIDI files...")
    total_length, file_count = process_path(path)

    if file_count > 0:
        print("\nSummary:")
        print(f"Total files processed: {file_count}")
        print(f"Total length: {total_length:.2f} seconds")
        print(f"Average length: {total_length / file_count:.2f} seconds")
    else:
        print("\nNo MIDI files found in the specified path.")


if __name__ == "__main__":
    main()
