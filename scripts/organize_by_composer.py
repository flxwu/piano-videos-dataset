import pandas as pd
import os
import shutil
import sys


def organize_by_composer(csv_path, midi_base_dir, output_base_dir, composer_name=None):
    # Read the CSV file
    df = pd.read_csv(csv_path)

    # If no composer specified, process all composers
    if composer_name is None:
        composers = df["canonical_composer"].unique()
        print(f"Found {len(composers)} composers")
    else:
        composers = [composer_name]

    # Process each composer
    for composer in composers:
        # Filter for the specific composer
        composer_df = df[df["canonical_composer"] == composer]

        if composer_df.empty:
            print(f"No files found for composer: {composer}")
            continue

        # Create composer directory
        composer_dir = os.path.join(
            output_base_dir, composer.replace("/", "_").replace(" ", "_")
        )
        os.makedirs(composer_dir, exist_ok=True)

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
    output_base_dir = "data/maestro_by_composer"

    # Get composer name from command line argument (optional)
    composer_name = None
    if len(sys.argv) > 1:
        composer_name = sys.argv[1]
        print(f"Processing composer: {composer_name}")
    else:
        print("Processing all composers")

    # Organize files
    organize_by_composer(csv_path, midi_base_dir, output_base_dir, composer_name)
