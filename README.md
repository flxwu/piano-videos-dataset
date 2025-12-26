Turn midis into synthetic self-playing-piano dataset using blender.

# Usage

#### Help:
```bash
PYTHONPATH=/home/stud/wfel/repos/piano-videos-dataset:$PYTHONPATH blender --python-use-system-env -b --python midi_to_piano/render.py -- --help
```

#### Render a single midi file:
```bash
# Make sure the folder `generated_data` exists
PYTHONPATH=/home/stud/wfel/repos/piano-videos-dataset:$PYTHONPATH blender --python-use-system-env -b --python midi_to_piano/render.py -- -m data/bach-1.mid -o generated_data -v True -r video
```


# Rendering on SLURM
See `submit_slurm_workers.py`.



# Development 

1. Install uv: https://docs.astral.sh/uv/
2. Then `uv sync`.


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

