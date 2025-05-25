import os
import shutil
import pandas as pd

MAESTRO_CSV_PATH = (
    "/home/wiss/koepa/code/piano-videos-dataset/data/maestro-v3.0.0/maestro-v3.0.0.csv"
)
BASE_PATH = "/storage/user/koepa/bach"
IMAGES_BASE_PATH = os.path.join(BASE_PATH, "input_images")
LABELS_BASE_PATH = os.path.join(BASE_PATH, "labels")
MIDI_BASE_PATH = os.path.join(BASE_PATH, "midi")
COMPOSER = "Johann Sebastian Bach"

# Read csv using pandas
df = pd.read_csv(MAESTRO_CSV_PATH)

# Filter rows where canonical_composer is 'Johann Sebastian Bach'
bach_df = df[df["canonical_composer"] == COMPOSER]

for i, row in bach_df.iterrows():
    split = row["split"]
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
# ls bach/input_images/test | wc -l && ls bach/labels/test | wc -l && ls bach/midi/test | wc -l
# ls bach/input_images/validation | wc -l && ls bach/labels/validation | wc -l && ls bach/midi/validation | wc -l
# ls bach/input_images/train | wc -l && ls bach/labels/train | wc -l && ls bach/midi/train | wc -l
