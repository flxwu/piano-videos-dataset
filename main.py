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
import bpy
import math
from pathlib import Path
from mathutils import Euler
from math import pi, radians
import sys
import os


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
except ModuleNotFoundError as exc:
    raise ModuleNotFoundError(
        "The 'mido' library is required for MIDI import. "
        "Install inside Blender’s Python with: pip install mido"
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

    for i in bpy.data.actions:
        for fcu in i.fcurves:
            for pt in fcu.keyframe_points:
                pt.interpolation = "CONSTANT"

    print(f"Imported MIDI: {midi_path.name}")


def camera(location, rotation):
    bpy.ops.object.add(type="CAMERA", location=location)
    cam = bpy.context.object
    cam.rotation_euler = Euler(
        (radians(rotation[0]), radians(rotation[1]), radians(rotation[2])), "XYZ"
    )
    cam.data.lens = 12
    bpy.context.scene.camera = cam
    return cam


# https://docs.blender.org/manual/en/latest/render/lights/light_object.html#sun-light
def lamp(location, type="SUN", energy=1, color=(1, 1, 1), target=None):
    # Lamp types: 'POINT', 'SUN', 'SPOT', 'HEMI', 'AREA'
    print("createLamp called")
    bpy.ops.object.add(type="LIGHT", location=location)
    obj = bpy.context.object
    obj.data.type = type
    obj.data.energy = energy
    obj.data.color = color

    # TODO: add target constraint
    # if target:
    #     trackToConstraint(obj, target)
    return obj


# -------------------------------------------------------------------
# RENDER TO MP4  (call this once everything is animated)
# -------------------------------------------------------------------
def render_to_video(
    output_path: str = "//piano_animation.mp4",
    fps: int | None = None,
    vcodec: str = "H264",
    container: str = "MPEG4",
    bitrate: int = 8000,
):
    """
    Renders the current scene frame-range to a single MP4/H.264 file.

    Parameters
    ----------
    output_path : str   Blender-style path, // is blend-file folder.
    fps         : int   If given, overrides scene FPS before rendering.
    vcodec      : str   FFmpeg video codec ID (H264, HEVC, PRORES, …).
    container   : str   FFmpeg container (MPEG4, MATROSKA, QUICKTIME…).
    bitrate     : int   kbit/s target; 0 = Blender default “Auto”.
    """
    sc = bpy.context.scene
    render = sc.render

    # optional FPS override
    if fps:
        render.fps = fps

    # basic output
    render.filepath = output_path
    render.image_settings.file_format = "FFMPEG"  # ⬅ file type
    render.image_settings.color_mode = "RGB"
    render.image_settings.quality = 90  # default
    render.ffmpeg.format = container  # mp4, mkv, …
    render.ffmpeg.codec = vcodec  # H264, HEVC = H265
    render.ffmpeg.constant_rate_factor = "MEDIUM"  # visual quality
    render.ffmpeg.video_bitrate = bitrate
    render.ffmpeg.gopsize = fps or sc.render.fps
    render.ffmpeg.max_b_frames = 2
    render.ffmpeg.use_max_b_frames = True
    render.ffmpeg.audio_codec = (
        "AAC"  # enable audio :contentReference[oaicite:7]{index=7}
    )
    render.ffmpeg.audio_bitrate = 192  # kb/s stereo
    render.ffmpeg.audio_channels = "STEREO"

    # make sure directory exists
    Path(bpy.path.abspath(output_path)).parent.mkdir(parents=True, exist_ok=True)

    print(f"▶  Rendering {sc.frame_start}-{sc.frame_end} to {output_path}")
    bpy.ops.render.render(
        animation=True
    )  # main call :contentReference[oaicite:1]{index=1}
    print("Rendering finished")


# ---------------------------------------------------------
# MAIN
# ---------------------------------------------------------


def render_from_midi(MIDI_PATH: str, OUTPUT_PATH: str, highlight_presses=True):
    clear_scene()

    camera(location=(95, -15, 100), rotation=(15, 0, 0))

    lamp(type="SUN", location=(105, 0, 100), energy=4)

    create_piano()
    if MIDI_PATH and Path(MIDI_PATH).exists():
        animate_from_midi(MIDI_PATH, highlight_presses)
    else:
        print("No MIDI file provided - keyboard only.")

    render_to_video(OUTPUT_PATH, fps=24)


if __name__ == "__main__":
    print(sys.version)
    print(sys.executable)
    print(os.getcwd())
    parser = argparse.ArgumentParser(prog="midi-to-piano", description="midi-to-piano")
    parser.add_argument("-m", "--render", type=bool, help="", default=False)
    parser.add_argument(
        "-m", "--midi", type=str, help="Path to an individual MIDI file", default=None
    )
    args = parser.parse_args()
    RENDERING_FLAG = args.render
    MIDI_PATH = args.midi
    if RENDERING_FLAG == "1":
        print(sys.argv)
        render_from_midi(
            MIDI_PATH,
            f"//renders/{Path(MIDI_PATH).stem}.mp4",
            highlight_presses=False,
        )
