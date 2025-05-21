"""
Utils for Blender.
"""

import os
from pathlib import Path
from math import radians
import sys
import bpy  # type: ignore # pylint: disable=import-error
from mathutils import Euler  # type: ignore # pylint: disable=import-error # https://docs.blender.org/api/current/mathutils.html


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


def render_to_frame_jpg(
    output_path: Path,
    frame_nr: int,
):
    sc = bpy.context.scene

    render = sc.render
    render.filepath = str(output_path)
    render.image_settings.file_format = "JPEG"

    sc.frame_set(frame_nr)
    print(f"▶  Rendering frame {frame_nr} to {output_path}")
    bpy_render_with_surpressed_logs(write_still=True)
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

    # set the number of samples to 30 for all rendering engines (CYCLES and EEVEE)
    sc.cycles.samples = 30
    sc.eevee.taa_render_samples = 30

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

    # make sure directory exists
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    print(f"▶  Rendering {sc.frame_start}-{sc.frame_end} to {output_path}")
    bpy_render_with_surpressed_logs(animation=True)
    print(f"▶  Rendering finished, saved to {output_path}")


def set_interpolation(interpolation: str) -> None:
    """
    Set the interpolation of all actions to the given interpolation.
    """
    for i in bpy.data.actions:
        for fcu in i.fcurves:
            for pt in fcu.keyframe_points:
                pt.interpolation = interpolation
