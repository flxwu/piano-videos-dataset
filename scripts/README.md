# Scripts Directory

This directory contains various utility scripts for working with MIDI files and piano data.

## Scripts Overview

### 1. `organize_by_composer.py`
Organizes MIDI files by composer from the MAESTRO dataset.

**Usage:**
```bash
uv run organize_by_composer.py <composer_name>
```

**Description:**
- Reads the MAESTRO dataset CSV file
- Filters MIDI files for a specific composer
- Creates a new directory structure organized by composer
- Copies relevant MIDI files to the composer's directory

### 2. `get_midi_length.py`
Calculates the length of MIDI files in seconds.

**Usage:**
```bash
uv run get_midi_length.py <path_to_midi_file_or_folder>
```

**Description:**
- Processes individual MIDI files or entire directories
- Calculates total length and average length of MIDI files
- Provides detailed output for each file processed
- Handles both single files and recursive directory processing

### 3. `overlay_labels_on_images.py`
Overlays piano key labels on generated frame images.

**Usage:**
```bash
uv run overlay_labels_on_images.py --input_dir=<input_images_dir> --pkl=<label_pkl_file> --output_dir=<output_dir>
```

**Description:**
- Takes input images and a pickle file containing piano key data
- Overlays piano key labels on the images
- Supports visualization of 88 piano keys
- Creates annotated images showing which keys are pressed
- Uses Arial font for labels (included in the directory)

### 4. `all-messages.py`
Utility script for debugging MIDI files by printing all MIDI messages.

**Description:**
- Reads a MIDI file and prints all messages with their absolute timestamps
- Useful for debugging MIDI file structure and content
- Currently configured to read from a specific test file

### 5. `split_files.py`
Splits files from a directory into equal-sized subfolders.

**Usage:**
```bash
uv run split_files.py <directory> <num_splits>
```

**Description:**
- Takes a source directory and number of desired splits
- Creates n equal-sized subfolders
- Distributes files evenly across the subfolders
- Useful for organizing large datasets into manageable chunks
- Preserves original filenames when moving to subfolders

## Notes

- The `arial.ttf` font file is included for use with the overlay script
- Some scripts assume specific directory structures (e.g., MAESTRO dataset format)
- Make sure to have the required dependencies installed before running the scripts
