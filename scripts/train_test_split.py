import os
import shutil
import pandas as pd
from pathlib import Path
import glob
import argparse

MAESTRO_CSV_PATH = (
    "/home/wiss/koepa/code/piano-videos-dataset/data/maestro-v3.0.0/maestro-v3.0.0.csv"
)
BASE_PATH = "/storage/user/koepa/maestro-visualized"

# Read csv using pandas
df = pd.read_csv(MAESTRO_CSV_PATH)
# Niccolò Paganini / Franz Liszt should become Niccolò_Paganini__Franz_Liszt
df['canonical_composer'] = df['canonical_composer'].str.replace(' / ', '__', regex=False).str.replace(r'\s+', '_', regex=True)
# midi_filename is prefixed with year, i.e. 2018/MIDI-Unprocessed_Chamber3_MID--AUDIO_10_R3_2018_wav--1.midi
# we want to remove the year from the midi_filename
df['midi_filename'] = df['midi_filename'].str.replace(r'^20\d{2}/', '', regex=True)
print(df['canonical_composer'].unique())

def convert_split(split):
    if split == 'train':
        return 'training'
    elif split == 'validation':
        return 'validation'
    elif split == 'test':
        return 'testing'
    else:
        raise ValueError(f"Invalid split: {split}")

# Create a lookup dictionary for O(1) access
midi_lookup = df.set_index('midi_filename')[['split', 'canonical_composer']].to_dict('index')

def process_files(dry_run=False):
    # Find all pkl files in labels directories (only one level down)
    for folder in sorted(os.listdir(BASE_PATH)):
        print(f"Processing folder: {folder}")
        folder_path = os.path.join(BASE_PATH, folder)
        if not os.path.isdir(folder_path):
            continue
            
        labels_dir = os.path.join(folder_path, 'labels')
        if not os.path.exists(labels_dir):
            print(f"No labels directory found for {folder_path}")
            continue
            
        pkl_pattern = os.path.join(labels_dir, "*.pkl")
        pkl_paths = glob.glob(pkl_pattern)
        print(f"Found {len(pkl_paths)} pkl files in {labels_dir}")
        for pkl_path in pkl_paths:
            # Get the base filename without extension
            # base_name will be e.g. MIDI-Unprocessed_Chamber3_MID--AUDIO_10_R3_2018_wav--1
            base_name = os.path.splitext(os.path.basename(pkl_path))[0]
            
            # Look up the corresponding MIDI file info
            midi_filename = f"{base_name}.midi"
            if midi_filename not in midi_lookup:
                print(f"No matching MIDI file found for {base_name}")
                continue
                
            # Get the split and composer from the lookup
            split = convert_split(midi_lookup[midi_filename]['split'])
            composer = midi_lookup[midi_filename]['canonical_composer']
            
            # Create target directories if they don't exist
            labels_target_dir = os.path.join(BASE_PATH, composer, 'labels', split)
            images_target_dir = os.path.join(BASE_PATH, composer, 'input_images', split)
            midi_target_dir = os.path.join(BASE_PATH, composer, 'midi', split)
            
            if not dry_run:
                os.makedirs(labels_target_dir, exist_ok=True)
                os.makedirs(images_target_dir, exist_ok=True)
                os.makedirs(midi_target_dir, exist_ok=True)
            
            # Move the corresponding input_images folder
            images_source = os.path.join(os.path.dirname(os.path.dirname(pkl_path)), 'input_images', base_name)
            if os.path.exists(images_source):
                images_target = os.path.join(images_target_dir, base_name)
                print(f"Moving images: {images_source} -> {images_target}")
                if not dry_run:
                    shutil.move(images_source, images_target)
            else:
                print(f"Input images folder not found for {base_name}")
                continue
                
            # Move the corresponding midi folder
            midi_source = os.path.join(os.path.dirname(os.path.dirname(pkl_path)), 'midi', base_name)
            if os.path.exists(midi_source):
                midi_target = os.path.join(midi_target_dir, base_name)
                print(f"Moving midi: {midi_source} -> {midi_target}")
                if not dry_run:
                    shutil.move(midi_source, midi_target)
            else:
                print(f"Midi folder not found for {base_name}")
                continue

            # Move the pkl file
            pkl_target = os.path.join(labels_target_dir, os.path.basename(pkl_path))
            print(f"Moving pkl: {pkl_path} -> {pkl_target}")
            if not dry_run:
                shutil.move(pkl_path, pkl_target)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Process and move files according to composer and split')
    parser.add_argument('--dry-run', action='store_true', help='Print what would be moved without actually moving files')
    args = parser.parse_args()
    print(f"Dry run: {args.dry_run}")
    process_files(dry_run=args.dry_run)

