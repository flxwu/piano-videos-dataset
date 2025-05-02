from pathlib import Path
import bpy
from math import radians
from mathutils import Euler

def camera(location, rotation):
    print("[INFO]: Creating camera")
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
    print("[INFO]: Creating lamp")
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
    output_path: str,
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
        "AAC" 
    )
    render.ffmpeg.audio_bitrate = 192  # kb/s stereo
    render.ffmpeg.audio_channels = "STEREO"


    # make sure directory exists
    Path(bpy.path.abspath(output_path)).parent.mkdir(parents=True, exist_ok=True)

    print(f"▶  Rendering {sc.frame_start}-{sc.frame_end} to {output_path}")
    bpy.ops.render.render(
        animation=True
    )
    print("Rendering finished")