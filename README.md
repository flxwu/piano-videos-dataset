## Installing packages in Blender on Linux


# Run script on Linux

## Prerequisites

- Blender
- FluidSynth
  - FluisSynth needs a soundfont to work. I tested using the [TimGM6mb.sf2](https://github.com/craffel/pretty-midi/blob/main/pretty_midi/TimGM6mb.sf2). Save it to `~/.fluidsynth/default_sound_font.sf2`.

## Install python packages into blender

Locate the python executable in your blender installation, for example "/home/stud/wfel/blender-4.4.3-linux-x64/4.4/python/bin/python3.10". 
Then do 

```bash
/home/stud/wfel/blender-4.4.3-linux-x64/4.4/python/bin/python3.10 -m pip install mido midi2audio
```


## Run script

```bash
PYTHONPATH=/home/stud/gruener/repos/piano-videos-dataset:$PYTHONPATH blender --python-use-system-env -b --python render.py -- -m data/bach-1.mid -o generated_data
```

Optional Flags:
- --render [true/false]
- --end_frame [number]
- --fps [number]
- --verbose
- --highlight_presses [true/false]


