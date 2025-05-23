#!/usr/bin/env python3

import os
import shutil
import argparse
from pathlib import Path
import math

def split_files_into_folders(source_dir: str, num_splits: int):
    """
    Split files from source directory into n equal-sized subfolders.
    
    Args:
        source_dir (str): Path to the source directory containing files
        num_splits (int): Number of subfolders to create
    """
    # Convert to Path object for easier handling
    source_path = Path(source_dir)
    
    # Get all files in the directory (excluding subdirectories)
    files = [f for f in source_path.iterdir() if f.is_file()]
    
    if not files:
        print(f"No files found in {source_dir}")
        return
    
    # Calculate files per folder
    total_files = len(files)
    files_per_folder = math.ceil(total_files / num_splits)
    
    # Create subfolders and move files
    for i in range(num_splits):
        # Create subfolder
        subfolder = source_path / f"split_{i+1}"
        subfolder.mkdir(exist_ok=True)
        
        # Calculate start and end indices for this split
        start_idx = i * files_per_folder
        end_idx = min((i + 1) * files_per_folder, total_files)
        
        # Move files to subfolder
        for file in files[start_idx:end_idx]:
            shutil.move(str(file), str(subfolder / file.name))
        
        print(f"Created split_{i+1} with {end_idx - start_idx} files")

def main():
    parser = argparse.ArgumentParser(description='Split files from a directory into n equal-sized subfolders')
    parser.add_argument('directory', help='Path to the directory containing files to split')
    parser.add_argument('num_splits', type=int, help='Number of subfolders to create')
    
    args = parser.parse_args()
    
    if not os.path.isdir(args.directory):
        print(f"Error: {args.directory} is not a valid directory")
        return
    
    if args.num_splits < 1:
        print("Error: Number of splits must be at least 1")
        return
    
    split_files_into_folders(args.directory, args.num_splits)

if __name__ == "__main__":
    main() 