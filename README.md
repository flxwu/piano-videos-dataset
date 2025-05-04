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
blender -b --python midi_to_piano/render.py -- --midi_path bach-1.mid --output_dir renders
```



