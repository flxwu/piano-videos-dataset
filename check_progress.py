import os
import pandas as pd
import argparse
from pathlib import Path


def check_progress(base_path, csv_path):
    # Read the CSV file
    df = pd.read_csv(csv_path)

    # Add a 'processed' column if it doesn't exist
    if "processed" not in df.columns:
        df["processed"] = False

    # Get all label directories
    base_path = Path(base_path)
    label_dirs = []
    for dir in os.listdir(base_path):
        label_dirs.append(os.path.join(base_path, dir, "labels"))

    # Process each label directory
    for label_dir in label_dirs:
        # Get all .pkl files in the labels directory
        # either the pkl files are just directly in the labels dir, or they are already in the split subdirs
        # in the latter case, we need to check the split subdirs
        pkl_files = [f for f in os.listdir(label_dir) if f.endswith(".pkl")]
        if len(pkl_files) == 0:
            for split_dir in os.listdir(label_dir):
                pkl_files.extend(
                    [
                        f
                        for f in os.listdir(os.path.join(label_dir, split_dir))
                        if f.endswith(".pkl")
                    ]
                )

        # For each PKL file, mark the corresponding MIDI file as processed
        for pkl_file in pkl_files:
            # Convert pkl filename to midi filename (remove .pkl extension)
            midi_filename = pkl_file[:-4] + ".midi"

            # Find the corresponding row in the dataframe
            mask = df["midi_filename"].str.endswith(midi_filename)
            if mask.any():
                df.loc[mask, "processed"] = True

    # Save the updated CSV
    output_path = csv_path.replace(".csv", "_with_progress.csv")
    df.to_csv(output_path, index=False)

    # Print statistics
    total_files = len(df)
    processed_files = df["processed"].sum()
    print(f"Total files: {total_files}")
    print(f"Processed files: {processed_files}")
    print(f"Progress: {processed_files / total_files * 100:.2f}%")
    print(f"Updated CSV saved to: {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Check processing progress of MIDI files"
    )
    parser.add_argument("base_path", help="Base path containing the processed files")
    parser.add_argument(
        "csv_path", help="Path to the CSV file containing MIDI filenames"
    )

    args = parser.parse_args()
    check_progress(args.base_path, args.csv_path)


if __name__ == "__main__":
    main()
