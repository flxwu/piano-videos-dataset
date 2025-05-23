#!/usr/bin/env python3

import os
import argparse
from pathlib import Path


def find_pkl_files(root_dir):
    """Find all .pkl files in the labels subdirectories of each subdirectory."""
    pkl_files = set()
    root_path = Path(root_dir)

    # Iterate through each subdirectory in root
    for subdir in root_path.iterdir():
        if not subdir.is_dir():
            continue

        # Look for labels directory within each subdir
        labels_dir = subdir / "labels"
        if labels_dir.exists():
            for file in labels_dir.iterdir():
                if file.suffix == ".pkl":
                    # Get the filename without extension
                    base_name = file.stem
                    pkl_files.add(base_name)
    return pkl_files


def cleanup_midi_files(pkl_folder, midi_folder):
    """Remove .midi files from midi_folder if corresponding .pkl exists in pkl_folder."""
    # Get all base names of .pkl files
    pkl_base_names = find_pkl_files(pkl_folder)

    # Counter for removed files
    removed_count = 0

    # Check each split folder in the midi folder
    for split_dir in Path(midi_folder).iterdir():
        if not split_dir.is_dir():
            continue

        # Check each .midi file in the split folder
        for midi_file in split_dir.iterdir():
            if midi_file.suffix == ".midi":
                base_name = midi_file.stem
                if base_name in pkl_base_names:
                    try:
                        midi_file.unlink()
                        print(f"Removed: {midi_file}")
                        removed_count += 1
                    except OSError as e:
                        print(f"Error removing {midi_file}: {e}")

    print(f"\nTotal files removed: {removed_count}")


def main():
    parser = argparse.ArgumentParser(
        description="Remove .midi files if corresponding .pkl exists in another folder"
    )
    parser.add_argument("pkl_folder", help="Folder containing .pkl files")
    parser.add_argument(
        "midi_folder", help="Folder containing .midi files to be cleaned up"
    )

    args = parser.parse_args()

    # Validate folders exist
    if not os.path.isdir(args.pkl_folder):
        print(f"Error: {args.pkl_folder} is not a valid directory")
        return
    if not os.path.isdir(args.midi_folder):
        print(f"Error: {args.midi_folder} is not a valid directory")
        return

    cleanup_midi_files(args.pkl_folder, args.midi_folder)


if __name__ == "__main__":
    main()
