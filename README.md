Turn midis into synthetic self-playing-piano dataset using blender.


# Development 

1. Install uv: https://docs.astral.sh/uv/
2. Then `uv sync`.

### Helper Scripts
A detailed description of all scripts is in `scripts/`.




# Prerequisites

- Blender: You can download the tar and unpack it somewhere on your machine. Remember the path you unpacked it to for later.
- FluidSynth
  - FluisSynth needs a soundfont to work. I tested using the [TimGM6mb.sf2](https://github.com/craffel/pretty-midi/blob/main/pretty_midi/TimGM6mb.sf2). Save it to `~/.fluidsynth/default_sound_font.sf2`.

#### Install python packages into blender

Locate the python executable in your blender installation, for example "/home/stud/wfel/blender-4.4.3-linux-x64/4.4/python/bin/python3.10". 
Then do 

```bash
/home/stud/wfel/blender-4.4.3-linux-x64/4.4/python/bin/python3.11 -m pip install mido midi2audio tqdm pretty_midi
```

# Usage

* `PATH_TO_REPO` is e.g. /home/wiss/koepa/code/piano-videos-dataset


#### Help:
```bash
PYTHONPATH=[PATH_TO_REPO]:$PYTHONPATH blender --python-use-system-env -b --python midi_to_piano/render.py -- --help

# usage: midi-to-piano [-h] -m MIDI_PATH [-f FPS] -o OUTPUT_DIR [-v VERBOSE] [-e END_FRAME] -r RENDER_FORMAT [-p HIGHLIGHT_PRESSES]

# midi-to-piano

# options:
#   -h, --help            show this help message and exit
#   -m MIDI_PATH, --midi_path MIDI_PATH
#                         String: Path to either a MIDI file, or a directory of MIDI files
#   -f FPS, --fps FPS     Integer: FPS for the rendered video
#   -o OUTPUT_DIR, --output_dir OUTPUT_DIR
#                         String: Path to the output directory
#   -v VERBOSE, --verbose VERBOSE
#                         Boolean: Verbose mode
#   -e END_FRAME, --end_frame END_FRAME
#                         Integer: End frame
#   -r RENDER_FORMAT, --render_format RENDER_FORMAT
#                         Enum: 'video' for mp4 output, 'frames' for individual frames (frame_000000.jpg, frame_000001.jpg, ...)
#   -p HIGHLIGHT_PRESSES, --highlight_presses HIGHLIGHT_PRESSES
#                         Boolean: If True, the pressed keys will be highlighted in orange
```

#### Render a single midi file:
```bash
# Make sure `generated_data` exists
PYTHONPATH=/home/stud/wfel/repos/piano-videos-dataset:$PYTHONPATH blender --python-use-system-env -b --python midi_to_piano/render.py -- -m data/bach-1.mid -o generated_data -v True -r video
```


# Rendering on SLURM

