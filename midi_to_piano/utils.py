"""
Utils for Blender.
"""

import os
from pathlib import Path
from math import radians
import sys
import bpy  # type: ignore # pylint: disable=import-error
from mathutils import Euler  # type: ignore # pylint: disable=import-error # https://docs.blender.org/api/current/mathutils.html

def get_output_paths(output_dir: Path, midi_path: Path) -> tuple[Path, Path, Path, Path]:
    frames_out_dir = output_dir / "videos" / midi_path.stem
    labels_out_dir = output_dir / "annotations" / midi_path.stem
    midi_out_dir = output_dir / "midi" / midi_path.stem
    wav_out_dir = output_dir / "audio" / midi_path.stem
    
    frames_out_dir.mkdir(parents=True, exist_ok=True)
    labels_out_dir.mkdir(parents=True, exist_ok=True)
    midi_out_dir.mkdir(parents=True, exist_ok=True)
    wav_out_dir.mkdir(parents=True, exist_ok=True)
    
    return frames_out_dir, labels_out_dir, midi_out_dir, wav_out_dir


def camera(location, rotation):
    # print("[INFO]: Creating camera")
    bpy.ops.object.add(type="CAMERA", location=location)
    cam = bpy.context.object
    cam.rotation_euler = Euler(
        (radians(rotation[0]), radians(rotation[1]), radians(rotation[2])), "XYZ"
    )
    cam.data.lens = 12
    bpy.context.scene.camera = cam
    return cam


# https://docs.blender.org/manual/en/latest/render/lights/light_object.html#sun-light
def lamp(location, light_type="SUN", energy=1, color=(1, 1, 1)):
    """
    Create a lamp.
    Lamp types: 'POINT', 'SUN', 'SPOT', 'HEMI', 'AREA'
    """
    # print("[INFO]: Creating lamp")
    bpy.ops.object.add(type="LIGHT", location=location)
    obj = bpy.context.object
    obj.data.type = light_type
    obj.data.energy = energy
    obj.data.color = color
    obj.data.cutoff_distance = 1000
    return obj


def bpy_render_with_surpressed_logs(**kwargs):
    # redirect output to log file
    logfile = "blender_render.log"
    open(logfile, "a").close()  # pylint: disable=unspecified-encoding # create log file if it doesn't exist
    old = os.dup(sys.stdout.fileno())
    sys.stdout.flush()
    os.close(sys.stdout.fileno())
    fd = os.open(logfile, os.O_WRONLY)

    # do the rendering
    bpy.ops.render.render(**kwargs)

    # disable output redirection
    os.close(fd)
    os.dup(old)
    os.close(old)

def set_crop_rectangle(sc, render):
    # set the number of samples to 30 for all rendering engines (CYCLES and EEVEE)
    sc.cycles.samples = 30
    sc.eevee.taa_render_samples = 30
    
    # initial borders (0–1, origin bottom-left)
    render.border_min_x, render.border_max_x = 0.12, 0.884
    render.border_min_y, render.border_max_y = 0.44, 0.64

    # make sure cropped size is divisible by 2 (required by FFmpeg/H.264)
    res_x, res_y = render.resolution_x, render.resolution_y
    if int((render.border_max_x - render.border_min_x) * res_x) & 1:
        render.border_max_x += 1 / res_x          # add 1 pixel
    if int((render.border_max_y - render.border_min_y) * res_y) & 1:
        render.border_max_y += 1 / res_y          # (height already OK here)


    # --- turn it on ----------------------------------------------------
    render.use_border        = True    # draw/render only the region
    render.use_crop_to_border = True   # make the output file **smaller**

def render_to_frame_jpg(
    output_path: Path,
    frame_nr: int,
    verbose: bool = False,
):
    sc = bpy.context.scene
    render = sc.render
    
    set_crop_rectangle(sc, render)
    render.filepath = str(output_path)
    render.image_settings.file_format = "JPEG"

    sc.frame_set(frame_nr)
    if verbose:
        print(f"▶  Rendering frame {frame_nr} to {output_path}")
    bpy_render_with_surpressed_logs(write_still=True)
    if verbose:
        print(f"▶  Rendering finished, saved to {output_path}")


# -------------------------------------------------------------------
# RENDER TO MP4  (call this once everything is animated)
# -------------------------------------------------------------------
def render_to_video(
    output_path: Path,
    fps: int | None = None,
    bitrate: int = 8000,
    start_frame: int = 0,
    end_frame: int = 250,
    verbose: bool = False,
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

    sc.frame_start = start_frame
    sc.frame_end = end_frame

    # optional FPS override
    if fps:
        render.fps = fps

    # basic output
    render.filepath = str(output_path)
    render.image_settings.file_format = "FFMPEG"  # ⬅ file type
    render.image_settings.color_mode = "RGB"
    render.image_settings.quality = 90  # default
    render.ffmpeg.format = "MPEG4"  # mp4, mkv, …
    render.ffmpeg.codec = "H264"  # H264, HEVC = H265
    render.ffmpeg.constant_rate_factor = "MEDIUM"  # visual quality
    render.ffmpeg.video_bitrate = bitrate
    render.ffmpeg.gopsize = fps or sc.render.fps
    render.ffmpeg.max_b_frames = 2
    render.ffmpeg.use_max_b_frames = True
    render.ffmpeg.audio_codec = "AAC"
    render.ffmpeg.audio_bitrate = 192  # kb/s stereo
    render.ffmpeg.audio_channels = "STEREO"
    
    set_crop_rectangle(sc, render)
    make_crop_even(sc, render)
    

    # make sure directory exists
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    if verbose:
        print(f"▶  Rendering {sc.frame_start}-{sc.frame_end} to {output_path}")
    bpy_render_with_surpressed_logs(animation=True)
    if verbose:
        print(f"▶  Rendering finished, saved to {output_path}. Rendered {sc.frame_start}-{sc.frame_end} frames.")
        
def make_crop_even(sc, render):
    res_x = render.resolution_x * render.resolution_percentage / 100
    res_y = render.resolution_y * render.resolution_percentage / 100

    # current pixel bounds
    left   = round(render.border_min_x * res_x)
    right  = round(render.border_max_x * res_x)
    bottom = round(render.border_min_y * res_y)
    top    = round(render.border_max_y * res_y)

    # force even width/height
    if (right - left) % 2:
        right -= 1                       # or left += 1
    if (top - bottom) % 2:
        top  -= 1

    # back to 0-1 range
    render.border_min_x = left  / res_x
    render.border_max_x = right / res_x
    render.border_min_y = bottom / res_y
    render.border_max_y = top   / res_y


def set_interpolation(interpolation: str) -> None:
    """
    Set the interpolation of all actions to the given interpolation.
    """
    for i in bpy.data.actions:
        for fcu in i.fcurves:
            for pt in fcu.keyframe_points:
                pt.interpolation = interpolation
