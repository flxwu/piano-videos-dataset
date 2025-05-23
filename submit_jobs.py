#!/usr/bin/env python3

"""
Submit jobs to the SLURM cluster.

Usage:
    uv run submit_jobs.py -m <list_of_midi_dirs> -o <output_dir> -b <blender_path>
    or
    uv run submit_jobs.py -M <midi_dir> -o <output_dir> -b <blender_path>

Example:
    uv run submit_jobs.py -M data/maestro_bach/ -o bach -b /home/wiss/koepa/code/piano-videos-dataset/blender-4.4.3-linux-x64/blender
"""

import argparse
import subprocess
import os
from pathlib import Path

# Get current user
CURRENT_USER = os.getenv("USER")


def create_sbatch_script(midi_dir, output_dir, BLENDER_PATH):
    """Create the sbatch script content."""
    script_content = f'''#!/bin/bash
#SBATCH --job-name="{midi_dir.split("/")[-1]}_renders"
#SBATCH --nodes=1
#SBATCH --cpus-per-task=4
#SBATCH --gres=gpu:1,VRAM:8
#SBATCH --mail-type=ALL
#SBATCH --mail-user=felix.wu@tum.de
#SBATCH --mem=16G
#SBATCH --time=180:00:00
#SBATCH --output=/storage/user/{CURRENT_USER}/slurm/logs/slurm-%j.out
#SBATCH --error=/storage/user/{CURRENT_USER}/slurm/logs/slurm-%j.out
#SBATCH --nodelist=node11,node12,node13,node14,node15,node16,node17,node18,node19
pwd; hostname; date
nvidia-smi

mkdir -p /storage/user/{CURRENT_USER}/{output_dir}

PYTHONPATH=/home/stud/{CURRENT_USER}/repos/piano-videos-dataset:$PYTHONPATH \\
{BLENDER_PATH} \\
  --python-use-system-env \\
  -b \\
  --python midi_to_piano/render.py \\
  -- \\
  -m {midi_dir} \\
  -o /storage/user/{CURRENT_USER}/{output_dir}
'''
    return script_content


def submit_job(script_content, job_name):
    """Submit the sbatch job and return the job ID."""
    # Create a temporary script file
    script_path = f"temp_{job_name}.sbatch"
    with open(script_path, "w") as f:
        f.write(script_content)

    # Make the script executable
    os.chmod(script_path, 0o755)

    # Submit the job
    result = subprocess.run(["sbatch", script_path], capture_output=True, text=True)

    # Clean up the temporary script
    os.remove(script_path)

    return result.stdout.strip()


def main():
    parser = argparse.ArgumentParser(
        description="Submit multiple piano video rendering jobs"
    )
    parser.add_argument(
        "-m",
        "--midi-dirs",
        nargs="+",
        required=False,
        help="List of MIDI directories to process",
    )
    parser.add_argument(
        "-M",
        "--midi-dir",
        required=False,
        help="Single directory containing MIDI subdirectories to process",
    )
    parser.add_argument(
        "-o", "--output-dir", required=True, help="Output directory for all renders"
    )
    parser.add_argument(
        "-b",
        "--blender-path",
        required=True,
        help="Path to the Blender executable, for example /home/stud/wfel/blender-4.4.3-linux-x64/blender",
    )

    args = parser.parse_args()

    # Check that either midi-dirs or midi-dir is provided
    if not args.midi_dirs and not args.midi_dir:
        print("Error: Either --midi-dirs or --midi-dir must be provided")
        return

    # Get list of MIDI directories
    if args.midi_dir:
        # Get all subdirectories from the provided directory
        midi_dirs = [str(d) for d in Path(args.midi_dir).iterdir() if d.is_dir()]
        if not midi_dirs:
            print(f"Error: No subdirectories found in {args.midi_dir}")
            return
    else:
        midi_dirs = args.midi_dirs

    # Create output subdirectories for each MIDI directory
    for midi_dir in midi_dirs:
        # Create a job name based on the directory name
        job_name = Path(midi_dir).name

        # Create output subdirectory
        output_subdir = os.path.join(args.output_dir, job_name)

        # Create the sbatch script content
        script_content = create_sbatch_script(
            midi_dir, output_subdir, args.blender_path
        )

        # Submit the job
        result = submit_job(script_content, job_name)
        print(f"Submitted job for {midi_dir} -> {output_subdir}")
        print(f"Job submission result: {result}")


if __name__ == "__main__":
    main()
