import pandas as pd
import os
import shutil
import sys


def organize_by_composer(csv_path, midi_base_dir, output_base_dir, composer_name):
    # Read the CSV file
    df = pd.read_csv(csv_path)

    # Filter for the specific composer
    composer_df = df[df["canonical_composer"] == composer_name]

    if composer_df.empty:
        print(f"No files found for composer: {composer_name}")
        return

    # Create composer directory
    # composer_dir = os.path.join(output_base_dir, composer_name)
    # os.makedirs(composer_dir, exist_ok=True)
    composer_dir = output_base_dir

    # Copy each MIDI file
    for _, row in composer_df.iterrows():
        midi_path = os.path.join(midi_base_dir, row["midi_filename"])
        if os.path.exists(midi_path):
            # Get just the filename without the directory structure
            midi_filename = os.path.basename(midi_path)
            # Copy to composer directory
            shutil.copy2(midi_path, os.path.join(composer_dir, midi_filename))
            print(f"Copied {midi_filename} to {composer_dir}")
        else:
            print(f"Warning: MIDI file not found: {midi_path}")


if __name__ == "__main__":
    # Paths
    csv_path = "data/maestro-v3.0.0/maestro-v3.0.0.csv"
    midi_base_dir = "data/maestro-v3.0.0"

    # Get composer name from command line argument
    if len(sys.argv) != 2:
        print("Usage: python organize_by_composer.py <composer_name>")
        sys.exit(1)
    composer_name = sys.argv[1]
    output_base_dir = f"data/maestro_{composer_name}"

    # Organize files
    organize_by_composer(csv_path, midi_base_dir, output_base_dir, composer_name)
