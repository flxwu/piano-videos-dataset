#!/usr/bin/env python3
"""
Utility script for overlaying a label-pkl for one MIDI on the generated frame images for that MIDI.

--input_mp4: Path to the mp4 file. (videos/midi_name.mp4)
--npz: Path to the label-npz file. (labels/midi_name.npz)
--output_dir: Path to the directory to save the overlayed images. (overlays/midi_name)

Usage:
uv run python scripts/overlay_labels_on_images.py --input_mp4=/storage/user/koepa/pianovision/final_data/videos/video_1.mp4 --npz=/storage/user/koepa/pianovision/final_data/labels/video_1.npz --output_dir overlays
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Tuple
import pickle
import cv2
import numpy as np
import numpy.typing as npt
from PIL import Image, ImageDraw, ImageFont

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

PIANO_KEYS = [
    "A0", "A#0", "B0",
    "C1", "C#1", "D1", "D#1", "E1", "F1", "F#1", "G1", "G#1", "A1", "A#1", "B1",
    "C2", "C#2", "D2", "D#2", "E2", "F2", "F#2", "G2", "G#2", "A2", "A#2", "B2",
    "C3", "C#3", "D3", "D#3", "E3", "F3", "F#3", "G3", "G#3", "A3", "A#3", "B3",
    "C4", "C#4", "D4", "D#4", "E4", "F4", "F#4", "G4", "G#4", "A4", "A#4", "B4",
    "C5", "C#5", "D5", "D#5", "E5", "F5", "F#5", "G5", "G#5", "A5", "A#5", "B5",
    "C6", "C#6", "D6", "D#6", "E6", "F6", "F#6", "G6", "G#6", "A6", "A#6", "B6",
    "C7", "C#7", "D7", "D#7", "E7", "F7", "F#7", "G7", "G#7", "A7", "A#7", "B7",
    "C8"
]  # fmt: skip


def load_font(font_size: int) -> ImageFont.ImageFont | ImageFont.FreeTypeFont:
    try:
        return ImageFont.truetype("arial.ttf", font_size)
    except OSError:
        return ImageFont.load_default()


def _text_size(
    draw: ImageDraw.ImageDraw,
    text: str,
    font: ImageFont.ImageFont | ImageFont.FreeTypeFont,
) -> Tuple[float, float]:
    """Return width and height of *text* for both new & old Pillow versions."""
    # Pillow ≥ 10.0 removed ``textsize``; use ``textbbox`` instead.
    if hasattr(draw, "textbbox"):
        left, top, right, bottom = draw.textbbox((0, 0), text, font=font)
        return right - left, bottom - top
    # Pillow < 10.0
    return draw.textsize(text, font=font)  # type: ignore[attr-defined]


# ---------------------------------------------------------------------------
# Core function
# ---------------------------------------------------------------------------


def overlay_array(
    image_path: Path | str,
    array: np.ndarray,
    output_path: Path | str,
    *,
    margin_ratio: float = 0.04,
    y_ratio: float = 0.6,
) -> None:
    """Overlay *array* onto *image_path* and save to *output_path*.

    Parameters
    ----------
    image_path : Path | str
        Path to the input JPG image.
    array : np.ndarray
        1-D NumPy array with exactly 88 elements.
    output_path : Path | str
        Destination for the annotated image.
    margin_ratio : float, optional
        Left/right margins as a fraction of image width.
    y_ratio : float, optional
        Vertical position of the text as a fraction of image height.
    font_size_ratio : float, optional
        Font size as a fraction of image height.
    """

    # --- load & validate ----------------------------------------------------
    img = Image.open(image_path).convert("RGB")
    width, height = img.size

    if array.size != 88:
        raise ValueError(f"Expected array of length 88, got {array.size}")

    # --- prepare drawing context -------------------------------------------
    draw = ImageDraw.Draw(img)

    # --- compute positions --------------------------------------------------
    margin = width * margin_ratio
    xs = np.linspace(margin, width - margin, array.size)
    y = int(height * y_ratio)

    # --- draw each value ----------------------------------------------------
    for i, value in enumerate(array):
        key = PIANO_KEYS[i]
        if value == 0:
            text = "0"
            font = load_font(font_size=30)
            tw, th = _text_size(draw, text, font)
            # draw.text(
            #     (float(xs[i] - tw / 2), y - th / 2), text, fill=(0, 0, 0), font=font
            # )
        else:
            text = key
            font = load_font(font_size=60)
            tw, th = _text_size(draw, text, font)
            draw.text(
                (float(xs[i] - tw / 2), y - th / 2), text, fill=(0, 255, 0), font=font
            )

    # --- save ---------------------------------------------------------------
    img.save(output_path)
    print(f"Saved overlay image to {output_path}")


# ---------------------------------------------------------------------------
# CLI wrapper
# ---------------------------------------------------------------------------


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Overlay an 88-entry NumPy array onto a JPG image.",
        epilog="Example: python overlay_array_on_image.py photo.jpg data.npy annotated.jpg",
    )
    parser.add_argument(
        "-i", "--input_mp4", type=Path, help="Input JPG image path", required=True
    )
    parser.add_argument(
        "-o", "--output_dir", type=Path, help="Output JPG image path", required=True
    )
    parser.add_argument(
        "-n", "--npz", type=Path, help="Path to .npz file", required=True
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    npz_path = Path(args.npz)
    input_mp4_path = Path(args.input_mp4)
    output_dir_path = Path(args.output_dir)
    output_dir_path.mkdir(parents=True, exist_ok=True)
    if not npz_path.exists():
        raise FileNotFoundError(f"File {npz_path} does not exist")
    if not input_mp4_path.exists() or not input_mp4_path.is_file():
        raise FileNotFoundError(
            f"File {input_mp4_path} does not exist or is not a file"
        )
    
    # Extract frames from mp4 file
    cap = cv2.VideoCapture(str(input_mp4_path))
    fps = cap.get(cv2.CAP_PROP_FPS)
    if fps != 25:
        print(f"Warning: Video FPS is {fps}, expected 25")
        
    # First pass: count frames and check npz keys
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    print(f"Video has {total_frames} frames")
    
    # Load npz to check keys
    with np.load(args.npz) as data:
        npz_keys = list(data.keys())
        npz_frame_count = len(npz_keys)
        print(f"NPZ file has {npz_frame_count} frame labels")
        
        if total_frames != npz_frame_count:
            print(f"Warning: Frame count mismatch! Video: {total_frames}, NPZ: {npz_frame_count}")
            
        # Check if all frame indices are present
        expected_keys = set(str(i) for i in range(total_frames))
        actual_keys = set(npz_keys)
        missing_keys = expected_keys - actual_keys
        extra_keys = actual_keys - expected_keys
        
        if missing_keys:
            print(f"Warning: Missing NPZ keys for frames: {sorted(missing_keys)[:10]}{'...' if len(missing_keys) > 10 else ''}")
        if extra_keys:
            print(f"Warning: Extra NPZ keys not matching video frames: {sorted(extra_keys)[:10]}{'...' if len(extra_keys) > 10 else ''}")
    
    # Load the npz data
    with np.load(args.npz) as data:
        frame_idx = 0
        while True:
            ret, frame = cap.read()
            if not ret:
                break
                
            # Convert BGR to RGB (OpenCV uses BGR by default)
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Save frame as temporary image
            temp_frame_path = output_dir_path / f"temp_frame_{frame_idx:06d}.jpg"
            Image.fromarray(frame_rgb).save(temp_frame_path)
            
            # Get corresponding label data if it exists
            if str(frame_idx) in data:
                arr = data[str(frame_idx)]  # Array of length 88
                
                overlay_array(
                    image_path=temp_frame_path,
                    array=arr,
                    output_path=output_dir_path / f"annotated_frame_{frame_idx:06d}.jpg",
                )
                
                # Remove temporary frame
                temp_frame_path.unlink()
            else:
                print(f"Warning: No label data for frame {frame_idx}")
                
            frame_idx += 1
    
    cap.release()


if __name__ == "__main__":
    main()
