import os
import pickle

TO_CHECK = ["debussy"]
BASE_DIR = "/storage/user/koepa"

for composer in TO_CHECK:
    labels_dir = f"{BASE_DIR}/{composer}/labels"
    images_dir = f"{BASE_DIR}/{composer}/input_images"

    for i, pkl_file in enumerate(os.listdir(labels_dir)):
        if i % 10 == 0:
            print(f"Verifying {i + 1} of {len(os.listdir(labels_dir))}")
        if not pkl_file.endswith(".pkl"):
            print(f"skipping check for non-pkl file {pkl_file}")
            continue
        base = pkl_file[:-4]
        image_folder = os.path.join(images_dir, base)
        pkl_path = os.path.join(labels_dir, pkl_file)
        if not os.path.isdir(image_folder):
            print(f"Image folder missing: {image_folder}")
            continue
        # Load the pickle file
        with open(pkl_path, "rb") as f:
            data = pickle.load(f)
        # Check for each key
        for key in data.keys():
            jpg_path = os.path.join(image_folder, f"{key}.jpg")
            if not os.path.isfile(jpg_path):
                print(f"Missing: {jpg_path}")
    print(f"Done checking {composer}")
