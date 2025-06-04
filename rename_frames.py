import os
import sys
from tqdm import tqdm


def rename_images(folder):
    # Check if the folder is a directory
    if not os.path.isdir(folder):
        print(f"Error: {folder} is not a directory.")
        return
    # List all jpg files that are named as numbers
    files = [f for f in os.listdir(folder) if f.endswith(".jpg") and f[:-4].isdigit()]
    # Sort files numerically
    for filename in tqdm(files):
        idx = int(filename[:-4])
        new_name = f"frame_{idx:06d}.jpg"
        src = os.path.join(folder, filename)
        dst = os.path.join(folder, new_name)
        # print(f"Renaming {filename} -> {new_name}")
        os.rename(src, dst)
    # Recursively process subdirectories
    for item in os.listdir(folder):
        subfolder = os.path.join(folder, item)
        if os.path.isdir(subfolder):
            rename_images(subfolder)
    print(f"Renamed {len(files)} files in {folder}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python rename_frames.py <folder>")
        sys.exit(1)
    # Call rename_images for all $foo/input_images subfolders
    for folder in os.listdir(sys.argv[1]):
        if os.path.isdir(os.path.join(sys.argv[1], folder, 'input_images')):
            print(f"Renaming frames in {folder}")
            rename_images(os.path.join(sys.argv[1], folder, 'input_images'))
        else:
            print(f"Skipping {folder}, no input_images subfolder found")
    print("Done")
