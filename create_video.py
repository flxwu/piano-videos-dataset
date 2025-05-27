#!/usr/bin/env python3

import subprocess
import cv2
import os
import midi2audio
from pathlib import Path


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


def create_video_from_frames(input_dir, output_file, midi_path, fps=25):
    """
    Create a video from a sequence of frames.

    Args:
        input_dir (str): Directory containing the input frames
        output_file (str): Path to save the output video
        fps (int): Frames per second for the output video
    """
    # Get all image files and sort them by numeric prefix
    image_files = sorted(
        [f for f in os.listdir(input_dir) if f.endswith((".png", ".jpg", ".jpeg"))],
        key=lambda x: int(x.split(".")[0]),  # Sort by numeric prefix before extension
    )
    print(image_files)

    if not image_files:
        print(f"No image files found in {input_dir}")
        return

    # Read the first image to get dimensions
    first_frame = cv2.imread(os.path.join(input_dir, image_files[0]))
    if first_frame is None:
        print(f"Error: Could not read first frame {image_files[0]}")
        return

    height, width, layers = first_frame.shape

    # Create video writer with H.264 codec
    fourcc = cv2.VideoWriter_fourcc(*"avc1")  # H.264 codec
    video = cv2.VideoWriter(output_file, fourcc, fps, (width, height))

    if not video.isOpened():
        print("Error: Could not create video writer. Trying alternative codec...")
        # Try alternative codec
        fourcc = cv2.VideoWriter_fourcc(*"XVID")
        video = cv2.VideoWriter(output_file, fourcc, fps, (width, height))
        if not video.isOpened():
            print("Error: Could not create video writer with any codec")
            return

    # Process each frame
    total_frames = len(image_files)
    for i, image_file in enumerate(image_files, 1):
        frame = cv2.imread(os.path.join(input_dir, image_file))
        if frame is None:
            print(f"Warning: Could not read frame {image_file}")
            continue

        # Ensure frame dimensions match
        if frame.shape[:2] != (height, width):
            print(f"Warning: Frame {image_file} has different dimensions. Resizing...")
            frame = cv2.resize(frame, (width, height))

        video.write(frame)

        # Print progress
        if i % 100 == 0:
            print(f"Processing frame {i}/{total_frames}")

    # Release the video writer
    video.release()
    print(f"\nVideo saved to: {output_file}")

    # Generate WAV file from MIDI
    wav_path = midi_to_wav(midi_path, output_file.with_suffix(".wav"))
    print(f"WAV file saved to: {wav_path}")

    # Add audio to video using ffmpeg
    temp_output = output_file.with_suffix(".temp.mp4")
    os.rename(output_file, temp_output)

    ffmpeg_cmd = [
        "ffmpeg",
        "-i",
        str(temp_output),
        "-i",
        str(wav_path),
        "-c:v",
        "copy",
        "-c:a",
        "aac",
        "-shortest",
        str(output_file),
    ]

    try:
        subprocess.run(ffmpeg_cmd, check=True, capture_output=True)
        os.remove(temp_output)  # Clean up temp file
        os.remove(wav_path)  # Clean up wav file
        print("Successfully added audio to video")
    except subprocess.CalledProcessError as e:
        print(f"Error adding audio to video: {e.stderr.decode()}")
        os.rename(temp_output, output_file)  # Restore original video if failed

    # Verify the video was created
    if not os.path.exists(output_file):
        print("Error: Video file was not created")
        return

    file_size = os.path.getsize(output_file)
    if file_size == 0:
        print("Error: Created video file is empty")
        return

    print(f"Video file size: {file_size / (1024 * 1024):.2f} MB")


def main():
    input_dir = "/storage/user/koepa/maestro-visualized/Johann_Sebastian_Bach/input_images/testing/MIDI-Unprocessed_03_R1_2008_01-04_ORIG_MID--AUDIO_03_R1_2008_wav--1"
    midi_path = "/home/wiss/koepa/code/piano-videos-dataset/midi_to_piano/temp_render/synthesized_MIDI-Unprocessed_03_R1_2008_01-04_ORIG_MID--AUDIO_03_R1_2008_wav--1.mid"
    output_file = "output_video.mp4"

    # Validate input directory
    if not os.path.isdir(input_dir):
        print(f"Error: {input_dir} is not a valid directory")
        return

    create_video_from_frames(input_dir, output_file, midi_path, fps=25)


if __name__ == "__main__":
    main()
