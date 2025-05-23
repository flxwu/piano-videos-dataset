"""
Piano + MIDI-driven animation
===========================================
Creates a full 88-key piano (A0-C8) and inserts keypress animations corresponding to a MIDI.

Run using
PYTHONPATH=/home/stud/gruener/repos/piano-videos-dataset:$PYTHONPATH blender --python-use-system-env -b --python render.py -- -m data/bach-1.mid -o generated_data
"""

import argparse
import os
import pickle
import sys
import math
from pathlib import Path
from tqdm import tqdm

import numpy as np
import midi2audio  # type: ignore
import mido  # type: ignore
import bpy  # type: ignore # pylint: disable=import-error
import pretty_midi  # type: ignore


from midi_to_piano.animation_result import AnimationResult
from midi_to_piano.blender_utils import clear_scene
from midi_to_piano.generate_labels import midi_to_binary_roll
from midi_to_piano.note_event import NoteEvent
from midi_to_piano.piano_rendering import create_piano
from midi_to_piano.utils import (
    camera,
    lamp,
    render_to_frame_jpg,
    render_to_video,
    set_interpolation,
    get_output_paths,
)


# -------------------------------------------------------------------
# CONFIGURATION
# -------------------------------------------------------------------

KEY_DOWN_DEG = 2.5  # rotation when pressed (degrees)
KEY_DOWN_Z = -0.08  # move downward
CLEAR_SCENE = True  # Set True to delete everything before building

FIRST_FRAME = 0

prefs = bpy.context.preferences
prefs.edit.keyframe_new_interpolation_type = "LINEAR"

ORANGE = (1.0, 0.5, 0.0, 1.0)  # <- highlight colour


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


def _setup_key_cache():
    """Create cache of key objects and their neutral colors"""
    key_cache = {
        o.name: o for o in bpy.data.objects if o.name.startswith(("White_", "Black_"))
    }
    used_frames = {name: set() for name in key_cache}

    # Store neutral colors
    neutral_colour = {
        name: obj.active_material.diffuse_color[:] for name, obj in key_cache.items()
    }

    return key_cache, used_frames, neutral_colour


def _initialize_keys(key_cache):
    """Set initial key positions and colors at frame 0"""
    for obj in key_cache.values():
        obj.delta_rotation_euler.x = 0.0
        obj.keyframe_insert("delta_rotation_euler", index=0, frame=0)
        obj.active_material.keyframe_insert("diffuse_color", frame=0)
        obj.location.z = 0
        obj.keyframe_insert("location", index=2, frame=0)


def animate_from_midi(
    fps: int,
    midi_path: Path, highlight_presses=True, verbose=False, end_frame=None
) -> AnimationResult:
    """
    Create piano key animations from a MIDI file.

    Args:
        midi_path: Path to the MIDI file
        highlight_presses: Whether to highlight pressed keys
        verbose: Enable verbose logging
    Returns:
        last_frame: The last frame of the animation
    """
    midi_path = midi_path.expanduser()
    if not midi_path.exists():
        raise FileNotFoundError(f"MIDI file not found: {midi_path}")

    key_cache, used_frames, neutral_colour = _setup_key_cache()
    _initialize_keys(key_cache)

    mid = mido.MidiFile(midi_path)
    bpy.context.scene.render.fps = fps

    # TODO: THIS ONLY WORKS FOR MIDI FILES WITH A SINGLE TRACK

    current_sec = 0.0
    last_frame = FIRST_FRAME

    # Store a dict of all animated notes {"note number": list of notes]
    notes: dict[int, list[NoteEvent]] = {}

    for msg in mid:
        current_sec += msg.time
        frame = FIRST_FRAME + round(current_sec * fps)
        if end_frame is not None and frame > end_frame:
            break

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

            if verbose:
                print(
                    f"Frame {free_frame} (frame_before_rounding {current_sec * fps}): {obj_name} {'down' if on else 'up'}, note {msg.note}"
                )

            # --- rotation key ----------------------------------------
            obj.delta_rotation_euler.x = math.radians(KEY_DOWN_DEG if on else 0)
            obj.keyframe_insert("delta_rotation_euler", index=0, frame=free_frame)
            obj.location.z = KEY_DOWN_Z if on else 0  # move downward
            obj.keyframe_insert("location", index=2, frame=free_frame)

            # --- colour key ------------------------------------------
            if highlight_presses:
                mat = obj.active_material
                mat.diffuse_color = ORANGE if on else neutral_colour[obj.name]
                mat.keyframe_insert("diffuse_color", frame=free_frame)

            last_frame = max(last_frame, free_frame)

            # Add the note to the list of notes
            if msg.note not in notes:
                notes[msg.note] = []
            notes[msg.note].append(NoteEvent(msg, on, free_frame))

    set_interpolation("CONSTANT")
    print(f"[INFO] ==== Successfully imported and animated MIDI: {midi_path.name} ====")
    return AnimationResult(fps=fps, end_frame=last_frame, events_for_note=notes)


# -------------------------------------------------------------------
# MIDI ➜ WAV  (uses midi2audio)
# -------------------------------------------------------------------
def midi_to_wav(midi_path: Path, wav_path: Path):
    """Convert *midi_path* to a 48 kHz 16-bit WAV via FluidSynth."""
    print(f"[INFO] Converting MIDI ({midi_path.name}) to WAV ({wav_path.name})")
    midi_path = Path(midi_path).expanduser()
    wav_path = Path(wav_path).expanduser()
    wav_path.parent.mkdir(parents=True, exist_ok=True)
    fs = midi2audio.FluidSynth()
    fs.midi_to_audio(str(midi_path), str(wav_path))
    print(
        f"[INFO] Finished converting MIDI ({midi_path.name}) to WAV ({wav_path.name})"
    )
    return wav_path


def add_audio_strip(wav_path: Path, channel: int = 1):
    """
    Insert a WAV into the VSE even if no Sequence Editor area exists.
    Returns the newly created strip.
    """
    print(f"[INFO] ==== Adding audio strip {wav_path} ====")
    wav_path = Path(wav_path).expanduser()
    scn = bpy.context.scene
    seq_ed = scn.sequence_editor or scn.sequence_editor_create()

    strip = seq_ed.sequences.new_sound(
        name=wav_path.stem,
        filepath=str(wav_path),
        channel=channel,
        frame_start=FIRST_FRAME,
    )
    print(f"[INFO] ==== Successfully added synthesized audio strip {wav_path} ====")

    return strip


# ---------------------------------------------------------
# MAIN
# ---------------------------------------------------------


def render_from_midi(
    midi_path: Path,
    output_dir: Path,
    fps: int,
    highlight_presses=False,
    verbose=False,
    end_frame=None,
    with_video=False,
):
    """Render a piano animation from a MIDI file to a video.

    Args:
        midi_path: Path to the input MIDI file
        output_path: Path where the output video will be saved
        fps: Frames per second for the output video
        highlight_presses: Whether to highlight pressed keys
        verbose: Enable verbose logging
    """
    clear_scene()

    camera(location=(95, 0, 80), rotation=(5, 0, 0))
    lamp(light_type="AREA", location=(95, -200, 150), energy=1 * (10**6))
    lamp(light_type="AREA", location=(0, -200, 150), energy=3 * (10**6))
    lamp(light_type="AREA", location=(200, -200, 150), energy=3 * (10**6))

    create_piano()
    animation_result: AnimationResult = animate_from_midi(
        fps=fps, midi_path=midi_path, highlight_presses=highlight_presses, verbose=verbose
    )
    end_frame = end_frame or animation_result.end_frame
    new_midi: pretty_midi.PrettyMIDI = animation_result.synthesize_new_midi()

    if with_video:
        curr_path = Path(os.path.abspath(__file__)).parent
        synthesized_midi_path = (
            curr_path / f"temp_render/synthesized_{midi_path.stem}.mid"
        )
        synthesized_midi_path.parent.mkdir(parents=True, exist_ok=True)
        new_midi.write(str(synthesized_midi_path))
        print(
            f"[INFO] Successfully saved synthesized MIDI to {synthesized_midi_path.name}"
        )

        wav = midi_to_wav(
            midi_path=synthesized_midi_path,
            wav_path=curr_path
            / f"temp_render/synthesized_{synthesized_midi_path.stem}.wav",
        )
        add_audio_strip(wav)
        # add one extra frame at end to make sure the last note is visible
        render_to_video(
            output_path=output_dir / "rendered_videos" / f"{midi_path.stem}.mp4",
            fps=fps,
            start_frame=FIRST_FRAME,
            end_frame=end_frame + 1,
            verbose=verbose,
        )

    # -- SAVE TRAINING DATA: Frame Images, Labels (Piano Roll), Midi
    frames_out_dir, midi_npzs_out_dir, labels_pkl_path = get_output_paths(
        output_dir, midi_path
    )

    # 1. Save Frame Images
    for frame_nr in tqdm(range(FIRST_FRAME, end_frame)):
        render_to_frame_jpg(
            output_path=frames_out_dir / f"{frame_nr}.jpg",
            frame_nr=frame_nr,
            verbose=verbose,
        )

    # 2. Save Labels
    binary_roll = midi_to_binary_roll(new_midi, frames_per_second=fps)
    # Convert binary roll to dictionary format
    label_dict: dict[int, np.ndarray] = {}
    for i, roll in enumerate(binary_roll):
        label_dict[i] = roll
    # Save labels in pickle format
    with open(labels_pkl_path, "wb") as f:
        pickle.dump(label_dict, f)

    # 3. Save MIDI files
    # Process MIDI files - create NPZ files for every 50 frames
    for i in range(0, len(binary_roll), 50):
        if i + 50 <= len(binary_roll):
            # Create a 50x88 array for the MIDI data
            midi_data = np.zeros((50, 88), dtype=np.float64)
            # Fill with the corresponding labels
            for j in range(50):
                if i + j < len(binary_roll):
                    midi_data[j] = binary_roll[i + j]

            # Save as NPZ file
            npz_filename = f"{i}-{i + 50}.npz"
            np.savez(str(midi_npzs_out_dir / npz_filename), midi=midi_data)


if __name__ == "__main__":
    print(
        f"[DEBUG]: {sys.version} | Executable {sys.executable} | Running in directory {os.getcwd()} | On Rendering Engine {bpy.context.scene.render.engine}"
    )
    parser = argparse.ArgumentParser(prog="midi-to-piano", description="midi-to-piano")
    parser.add_argument(
        "-m",
        "--midi_path",
        type=str,
        help="Path to either a MIDI file, or a directory of MIDI files",
        default=None,
        required=True,
    )
    parser.add_argument(
        "-f",
        "--fps",
        type=str,
        help="FPS for the rendered video",
        default=25,
        required=False,
    )
    parser.add_argument(
        "-o",
        "--output_dir",
        type=str,
        help="Path to the output directory",
        default=None,
        required=True,
    )
    parser.add_argument(
        "-v", "--verbose", type=bool, help="Verbose mode", default=False, required=False
    )
    parser.add_argument(
        "-e", "--end_frame", type=int, help="End frame", default=None, required=False
    )
    parser.add_argument(
        "-w",
        "--with_video",
        type=bool,
        help="Render video",
        default=False,
        required=False,
    )
    parser.add_argument(
        "-p",
        "--highlight_presses",
        type=bool,
        help="Highlight presses",
        default=False,
        required=False,
    )
    argv = (
        sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
    )  # blender passes script arguments after "--"
    args = parser.parse_args(argv)
    MIDI_PATH = Path(args.midi_path)
    OUTPUT_DIR = Path(args.output_dir)
    FPS = int(args.fps)
    VERBOSE = args.verbose
    END_FRAME = args.end_frame
    HIGHLIGHT_PRESS = args.highlight_presses
    WITH_VIDEO = args.with_video
    if not MIDI_PATH.exists():
        raise FileNotFoundError(f"MIDI file not found: {MIDI_PATH}")

    if not OUTPUT_DIR.exists() or not OUTPUT_DIR.is_dir():
        raise FileNotFoundError(f"Output directory not found: {OUTPUT_DIR}")

    if MIDI_PATH.is_dir():
        midi_files = list(MIDI_PATH.glob("*.midi"))
        for i, midi_file in enumerate(midi_files):
            _, _, labels_pkl_path = get_output_paths(OUTPUT_DIR, midi_file)
            if labels_pkl_path.exists():
                print(f"[INFO] Skipping {midi_file} because labels already exist")
                continue
            render_from_midi(
                midi_path=midi_file,
                output_dir=OUTPUT_DIR,
                highlight_presses=HIGHLIGHT_PRESS,
                fps=FPS,
                verbose=VERBOSE,
                end_frame=END_FRAME,
                with_video=WITH_VIDEO,
            )
            print(f"[INFO] Rendered {i}/{len(midi_files)} from directory {MIDI_PATH}")
    else:
        render_from_midi(
            midi_path=MIDI_PATH,
            output_dir=OUTPUT_DIR,
            highlight_presses=HIGHLIGHT_PRESS,
            fps=FPS,
            verbose=VERBOSE,
            end_frame=END_FRAME,
            with_video=WITH_VIDEO,
        )
