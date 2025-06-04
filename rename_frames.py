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
    if len(files) == 0:
        print(f"Skipping {folder}, no jpg files found")
        return
    # Sort files numerically
    files.sort(key=lambda x: int(x[:-4]))
    for idx, filename in tqdm(enumerate(files, 1)):
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
    rename_images(sys.argv[1])
