import os
import shutil
import pandas as pd

MAESTRO_CSV_PATH = (
    "/home/wiss/koepa/code/piano-videos-dataset/data/maestro-v3.0.0/maestro-v3.0.0.csv"
)
BASE_PATH = "/storage/user/koepa/maestro-visualized"

# Read csv using pandas
df = pd.read_csv(MAESTRO_CSV_PATH)

for composer_dir in os.listdir(BASE_PATH):
    # if composer_dir/training, composer_dir/testing, composer_dir/validation exist, skip
    if (
        os.path.exists(os.path.join(BASE_PATH, composer_dir, "training"))
        and os.path.exists(os.path.join(BASE_PATH, composer_dir, "testing"))
        and os.path.exists(os.path.join(BASE_PATH, composer_dir, "validation"))
    ):
        print(f"Skipping {composer_dir} because it already has splits")
        continue

    composer_name = composer_dir.replace("_", " ")
    # Filter rows where canonical_composer is 'Johann Sebastian Bach'
    composer_df = df[df["canonical_composer"] == composer_name]

    IMAGES_BASE_PATH = os.path.join(BASE_PATH, composer_dir, "input_images")
    LABELS_BASE_PATH = os.path.join(BASE_PATH, composer_dir, "labels")
    MIDI_BASE_PATH = os.path.join(BASE_PATH, composer_dir, "midi")

    for i, row in composer_df.iterrows():
        # train -> training, test -> testing, validation -> validation
        if row["split"] == "train":
            split = "training"
        elif row["split"] == "test":
            split = "testing"
        elif row["split"] == "validation":
            split = "validation"
        else:
            print(f"Unknown split: {row['split']}")
            continue
        midi_name = row["midi_filename"]
        if "/" in midi_name:
            midi_name = midi_name.split("/")[1]  # path starts with year/
        midi_name = midi_name.replace(".midi", "")
        image_dir_for_midi = os.path.join(IMAGES_BASE_PATH, midi_name)
        label_pkl_for_midi = os.path.join(LABELS_BASE_PATH, f"{midi_name}.pkl")
        midi_dir_for_midi = os.path.join(MIDI_BASE_PATH, midi_name)
        # check that both exist
        if os.path.exists(image_dir_for_midi):
            new_img_dir = os.path.join(IMAGES_BASE_PATH, split)
            if not os.path.exists(new_img_dir):
                os.makedirs(new_img_dir)
            print(f"Moving {image_dir_for_midi} to {new_img_dir}")
            shutil.move(image_dir_for_midi, new_img_dir)
        else:
            print(f"Image directory for {midi_name} does not exist")

        if os.path.exists(label_pkl_for_midi):
            new_label_dir = os.path.join(LABELS_BASE_PATH, split)
            if not os.path.exists(new_label_dir):
                os.makedirs(new_label_dir)
            print(f"Moving {label_pkl_for_midi} to {new_label_dir}")
            shutil.move(label_pkl_for_midi, new_label_dir)
        else:
            print(f"Label pickle for {midi_name} does not exist")

        if os.path.exists(midi_dir_for_midi):
            new_midi_dir = os.path.join(MIDI_BASE_PATH, split)
            if not os.path.exists(new_midi_dir):
                os.makedirs(new_midi_dir)
            print(f"Moving {midi_dir_for_midi} to {new_midi_dir}")
            shutil.move(midi_dir_for_midi, new_midi_dir)
        else:
            print(f"MIDI file for {midi_name} does not exist")


# Run these commands to check the splits are correct
# ls Johann_Sebastian_Bach/input_images/testing | wc -l && ls Johann_Sebastian_Bach/labels/testing | wc -l && ls Johann_Sebastian_Bach/midi/testing | wc -l
# ls Johann_Sebastian_Bach/input_images/validation | wc -l && ls Johann_Sebastian_Bach/labels/validation | wc -l && ls Johann_Sebastian_Bach/midi/validation | wc -l
# ls Johann_Sebastian_Bach/input_images/training | wc -l && ls Johann_Sebastian_Bach/labels/training | wc -l && ls Johann_Sebastian_Bach/midi/training | wc -l
