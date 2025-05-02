"""
Piano + MIDI‑driven animation
===========================================
Creates a full 88‑key piano (A0–C8) and inserts keypress animations corresponding to a MIDI.

Quick usage
-----------
1. Install the `mido` python package into blender's environment (import pip; pip.main(['install', 'mido', '--user']))
2. Put your MIDI file somewhere and set `MIDI_PATH` below.
3. In a fresh scene, open the *Scripting* tab, paste this script, and click
   **Run Script**.
4. Press **Spacebar** to watch the playback.
"""

import argparse
import copy
import bpy
import math
from pathlib import Path
from mathutils import Euler
from math import pi, radians
import sys
import os

# Add the project directory to Blender's sys.path to import utils
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
if PROJECT_DIR not in sys.path:
    sys.path.append(PROJECT_DIR)

from utils import camera, lamp, render_to_video


# -------------------------------------------------------------------
# CONFIGURATION
# -------------------------------------------------------------------
SCALE_FACTOR = 100
WHITE_KEY_W = 0.030 * SCALE_FACTOR
WHITE_KEY_H = 0.030 * SCALE_FACTOR
WHITE_KEY_L = 0.230 * SCALE_FACTOR  # Tiefe

BLACK_KEY_W = 0.016 * SCALE_FACTOR
BLACK_KEY_H = 0.045 * SCALE_FACTOR
BLACK_KEY_L = 0.120 * SCALE_FACTOR

KEY_DOWN_DEG = 7  # rotation when pressed (degrees)

KEY_GAP = 0.3
CLEAR_SCENE = True  # Set True to delete everything before building

FIRST_FRAME = 1

prefs = bpy.context.preferences
prefs.edit.keyframe_new_interpolation_type = "LINEAR"

ORANGE = (1.0, 0.5, 0.0, 1.0)  # <- highlight colour

# -------------------------------------------------------------------

# ---------------------------------------------------------
# CHECK DEPENDENCIES
# ---------------------------------------------------------
try:
    import mido
    import midi2audio
except ModuleNotFoundError as exc:
    raise ModuleNotFoundError(
        "The 'mido' and 'midi2audio' libraries are required. "
        "Install inside Blender's Python with: pip install mido midi2audio"
    ) from exc


def clear_scene():
    """Delete all objects in the current scene."""
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)


def set_origin_at_back(obj, length):
    """Move cursor to the rear edge of *obj* and set that as the origin."""
    x, y, _ = obj.location
    bpy.context.scene.cursor.location = (x, y + length / 2, 0)
    bpy.ops.object.origin_set(type="ORIGIN_CURSOR", center="MEDIAN")


def build_key(
    name: str,
    width: float,
    height: float,
    length: float,
    left: float,
    top: float,
    is_black: bool,
):
    """Create a key whose **left edge** sits at *left* and **top edge** sits at *top* and return the object.
    note: length = "tiefe"
    """
    cube_x = left + width / 2
    cube_y = top - length / 2
    bpy.ops.mesh.primitive_cube_add(size=1, location=(cube_x, cube_y, height))

    key = bpy.context.object
    key.name = name
    key.scale = (width, length, height)
    key.rotation_mode = "XYZ"

    # UNIQUE material per key -------------------------------------
    mat = bpy.data.materials.new(f"{name}_Mat")
    base_colour = (0, 0, 0, 1) if is_black else (0.9, 0.9, 0.9, 1)
    mat.diffuse_color = base_colour
    key.data.materials.append(mat)

    set_origin_at_back(key, length)
    return key


def create_piano():
    """Build an 88-key keyboard in a collection named 'Piano'."""

    # If the collection already exists, reuse it
    piano_col = bpy.data.collections.get("Piano")
    if piano_col is None:
        piano_col = bpy.data.collections.new("Piano")
        bpy.context.scene.collection.children.link(piano_col)

    # White note names A0–C8 (52 keys)
    white_notes = [
        "A0",
        "B0",
        *[f"{n}{o}" for o in range(1, 8) for n in ("C", "D", "E", "F", "G", "A", "B")],
        "C8",
    ]

    left = 10.0  # current left edge position along X
    pending_black = []  # tuples (center_x, note_name)

    for idx, note in enumerate(white_notes):
        build_key(
            name=f"White_{note}",
            width=WHITE_KEY_W,
            height=WHITE_KEY_H,
            length=WHITE_KEY_L,
            left=left,
            top=WHITE_KEY_L,
            is_black=False,
        )

        # No black keys after last white key
        if idx == len(white_notes) - 1:
            break

        # Decide if a black key follows this white key (no sharps after E or B)
        if note[0] not in {"E", "B"}:
            black_center = left + WHITE_KEY_W  # halfway between this and next white
            pending_black.append((black_center, note))

        left += WHITE_KEY_W + KEY_GAP  # advance left edge for next white

    # Build black keys after all whites for clarity
    for center_x, base_note in pending_black:
        bkey = build_key(
            name=f"Black_{base_note}#",
            width=BLACK_KEY_W,
            height=BLACK_KEY_H,
            length=BLACK_KEY_L,
            left=center_x - BLACK_KEY_W / 2,
            top=WHITE_KEY_L,
            is_black=True,
        )
        # Lift black keys higher than whites
        bkey.location.z += (WHITE_KEY_H - BLACK_KEY_H) / 2

    print(
        f"Piano generated with {len(white_notes)} white and {len(pending_black)} black keys"
    )


# ---------------------------------------------------------
# MIDI → KEYFRAME ANIMATION
# ---------------------------------------------------------


def midi_note_to_object_name(note_number: int) -> str:
    names = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
    name = names[note_number % 12]
    octave = (note_number // 12) - 1
    if "#" in name:
        return f"Black_{name[0]}{octave}#"
    return f"White_{name}{octave}"


def animate_from_midi(midi_path: str | Path, highlight_presses=True):
    midi_path = Path(midi_path).expanduser()
    if not midi_path.exists():
        raise FileNotFoundError(f"MIDI file not found: {midi_path}")

    mid = mido.MidiFile(midi_path)
    fps = bpy.context.scene.render.fps or 24

    key_cache = {
        o.name: o for o in bpy.data.objects if o.name.startswith(("White_", "Black_"))
    }
    # remember every frame already keyed for each key object
    used_frames: dict[str, set[int]] = {name: set() for name in key_cache}

    # --- put every key at rest on frame 0 ---------------------------
    for obj in key_cache.values():
        obj.delta_rotation_euler.x = 0.0  # neutral angle
        obj.keyframe_insert("delta_rotation_euler", index=0, frame=0)
    # ----------------------------------------------------------------

    # --- store each key's neutral colour & keyframe it at frame 0
    neutral_colour = {
        name: obj.active_material.diffuse_color[:]  # copy()
        for name, obj in key_cache.items()
    }
    for obj in key_cache.values():
        mat = obj.active_material
        mat.keyframe_insert("diffuse_color", frame=0)

    current_sec = 0.0
    # TODO: THIS ONLY WORKS FOR MIDI FILES WITH A SINGLE TRACK
    
    # --- CREATE NEW MIDI FILE WITH TICKS PER BEAT
    new_mid  = mido.MidiFile(ticks_per_beat=mid.ticks_per_beat)
    new_track = mido.MidiTrack()
    new_mid.tracks.append(new_track)

    current_abs_sec   = 0.0                # absolute time while we read
    last_quantised_sec = FIRST_FRAME / FPS # where the very first message will land

    # default tempo until we see the first set_tempo meta
    tempo = mido.bpm2tempo(120)            # 500 000 μs per quarter
    # ---
    
    for msg in mid:
        current_sec += msg.time
        frame = FIRST_FRAME + round(current_sec * fps)

        if msg.type in {"note_on", "note_off"}:
            on = msg.type == "note_on" and msg.velocity > 0
            obj_name = midi_note_to_object_name(msg.note)
            obj = key_cache.get(obj_name)
            if obj is None:
                print(f"ERROR: KEY {obj_name} NOT FOUND")
                continue

            # --- THIS IS AN UGLY HACK
            # If the frame-rate isn't very high, it's possible that we get a note_off and note_on for the same note within the period of 1 frame.
            # If this happens, we schedule the second event to the next frame, to prevent 'hiding this keypress' in the video.
            free_frame = frame
            while free_frame in used_frames[obj.name]:  # already keyed?
                free_frame += 1  # bump one frame
            used_frames[obj.name].add(free_frame)  # reserve it
            # ---------------------------------------------------------------

            print(
                f"Frame {free_frame} (frame_before_rounding {current_sec * fps}): {obj_name} {'down' if on else 'up'}, note {msg.note}"
            )

            # --- rotation key ----------------------------------------
            obj.delta_rotation_euler.x = math.radians(KEY_DOWN_DEG if on else 0)
            obj.keyframe_insert("delta_rotation_euler", index=0, frame=free_frame)

            # --- colour key ------------------------------------------
            if highlight_presses:
                mat = obj.active_material
                mat.diffuse_color = ORANGE if on else neutral_colour[obj.name]
                mat.keyframe_insert("diffuse_color", frame=free_frame)
            
            # ==== COPY TO NEW MIDI FILE ====
            quantised_sec  = free_frame / FPS
            delta_sec  = quantised_sec - last_quantised_sec
            last_quantised_sec = quantised_sec
            # Convert the delta *seconds* → *ticks* expected by the writer
            delta_ticks = round(
                mido.second2tick(delta_sec,
                                mid.ticks_per_beat,
                                tempo)
            )
            # It must be a non-negative int
            delta_ticks = max(0, int(delta_ticks))
            # Copy the message so the original stays intact
            new_msg = copy.deepcopy(msg)
            new_msg.time = delta_ticks
            new_track.append(new_msg)
            # =============================
        # Keep track of tempo changes so conversion stays correct
        if msg.type == 'set_tempo':
            tempo = msg.tempo

    for i in bpy.data.actions:
        for fcu in i.fcurves:
            for pt in fcu.keyframe_points:
                pt.interpolation = "CONSTANT"

    curr_path = Path(os.path.abspath(__file__)).parent
    new_mid.save(curr_path / "temp_render/midi_audio.mid")
    WAV = midi_to_wav(curr_path / "temp_render/midi_audio.mid")
    add_audio_strip(WAV)
    print(f"[INFO] Imported MIDI: {midi_path.name}")



# -------------------------------------------------------------------
# MIDI ➜ WAV  (uses midi2audio)
# -------------------------------------------------------------------
def midi_to_wav(midi_path: str | Path,
                wav_path: str = "//temp_render/midi_audio.wav"):
    """Render *midi_path* to a 48 kHz 16-bit WAV via FluidSynth."""       
    midi_path = Path(midi_path).expanduser()
    wav_path  = Path(bpy.path.abspath(wav_path))
    wav_path.parent.mkdir(parents=True, exist_ok=True)

    if wav_path.exists():
        return wav_path           # skip if we rendered it already

    fs = midi2audio.FluidSynth()
    fs.midi_to_audio(str(midi_path), str(wav_path))
    return wav_path

def add_audio_strip(wav_path: Path, channel: int = 1):
    """Insert *wav_path* at frame-0 in the VSE; create the editor if absent."""
    scn = bpy.context.scene
    scn.sequence_editor_create()                       # ensures VSE exists
    bpy.ops.sequencer.sound_strip_add(
        filepath=str(wav_path),
        frame_start=0,
        channel=channel)                               


# ---------------------------------------------------------
# MAIN
# ---------------------------------------------------------


def render_from_midi(MIDI_PATH: str, OUTPUT_PATH: str, fps: int, highlight_presses=False):
    clear_scene()

    camera(location=(95, -15, 100), rotation=(15, 0, 0))

    lamp(type="SUN", location=(105, 0, 100), energy=4)

    create_piano()
    if MIDI_PATH and Path(MIDI_PATH).exists():
        animate_from_midi(MIDI_PATH, highlight_presses)
    else:
        raise Exception("ERROR: No MIDI file provided.")

    render_to_video(output_path=OUTPUT_PATH, fps=fps)


if __name__ == "__main__":
    print(f"[DEBUG]: {sys.version} | Executable {sys.executable} | Running in directory {os.getcwd()}")
    parser = argparse.ArgumentParser(prog="midi-to-piano", description="midi-to-piano")
    parser.add_argument(
        "-m", "--midi_path", type=str, help="Path to either a MIDI file, or a directory of MIDI files", default=None, required=True
    )
    parser.add_argument(
        "-f", "--fps", type=str, help="FPS for the rendered video", default=24, required=False
    )
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else [] # blender passes script arguments after "--"
    args = parser.parse_args(argv)
    MIDI_PATH = args.midi_path
    FPS = int(args.fps)
    render_from_midi(
        MIDI_PATH=MIDI_PATH,
        OUTPUT_PATH=f"//renders/{Path(MIDI_PATH).stem}.mp4",
        highlight_presses=False,
        fps=FPS,
    )
