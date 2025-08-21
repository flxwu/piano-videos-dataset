#!/usr/bin/env python3

"""
Submit jobs to the SLURM cluster for Maestro dataset processing.

Usage:
    uv run submit_jobs.py -c <csv_path> -o <output_dir> -b <blender_path>

Example:
    uv run submit_jobs.py -c data/maestro-v3.0.0/maestro-v3.0.0.csv -o /storage/user/koepa/pianovision/maestro-visualized-new -b /home/wiss/koepa/code/piano-videos-dataset/blender-4.4.3-linux-x64/blender
"""

import argparse
import subprocess
import os
import csv
from pathlib import Path
from collections import defaultdict

# Get current user
CURRENT_USER = os.getenv("USER")


def create_sbatch_script(midi_files, output_dir, job_name, BLENDER_PATH):
    """Create the sbatch script content."""
    # Convert list of MIDI files to space-separated string
    midi_files_str = " ".join(midi_files)
    
    script_content = f'''#!/bin/bash
#SBATCH --job-name="{job_name}"
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

mkdir -p {output_dir}

PYTHONPATH=/home/stud/{CURRENT_USER}/repos/piano-videos-dataset:$PYTHONPATH \\
{BLENDER_PATH} \\
  --python-use-system-env \\
  -b \\
  --python midi_to_piano/render.py \\
  -- \\
  -m {midi_files_str} \\
  -o {output_dir} \\
  -r video \\
  -v True
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
    # result is something like `Submitted batch job 1406202`
    
    if result.returncode != 0 or "Submitted batch job" not in result.stdout:
        raise Exception(f"Error submitting job for {job_name}: {result.stderr}\n{result.stdout}")
    
    # rename the file to the job id
    os.rename(script_path, f"job_id_{result.stdout.strip().split(" ")[-1]}.sbatch") # e.g. 1406202.sbatch

    return result.stdout.strip()


def read_maestro_csv(csv_path):
    """Read the Maestro CSV file and group MIDI files by worker_id."""
    worker_midi_files = defaultdict(list)
    
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            worker_id = int(row['worker_id'])
            midi_filename = row['midi_filename']
            # Construct full path to MIDI file
            midi_path = f"data/maestro-v3.0.0/{midi_filename}"
            worker_midi_files[worker_id].append(midi_path)
    
    return worker_midi_files


def main():
    parser = argparse.ArgumentParser(
        description="Submit multiple piano video rendering jobs for Maestro dataset"
    )
    parser.add_argument(
        "-c",
        "--csv-path",
        required=True,
        help="Path to the Maestro CSV file (e.g., data/maestro-v3.0.0/maestro-v3.0.0.csv)",
    )
    parser.add_argument(
        "-o", "--output-dir", required=True, help="Output base directory for all renders"
    )
    parser.add_argument(
        "-b",
        "--blender-path",
        required=True,
        help="Path to the Blender executable, for example /home/stud/wfel/blender-4.4.3-linux-x64/blender",
    )

    args = parser.parse_args()

    # Read the CSV file and group MIDI files by worker_id
    print(f"Reading Maestro CSV file: {args.csv_path}")
    worker_midi_files = read_maestro_csv(args.csv_path)
    
    print(f"Found {len(worker_midi_files)} workers with MIDI files:")
    for worker_id, midi_files in worker_midi_files.items():
        print(f"  Worker {worker_id}: {len(midi_files)} MIDI files")

    # Create the sbatch script content for each worker
    output_base_dir = Path(args.output_dir)

    # TEMP: Filter for workers
    worker_midi_files = {k: v for k, v in worker_midi_files.items() if k in list(range(0,9))}
    
    for worker_id, midi_files in worker_midi_files.items():
        # Create a job name based on the worker_id
        job_name = f"maestro_worker_{worker_id}_renders"
        print(f"Processing {job_name} with {len(midi_files)} MIDI files...")
        
        output_dir = output_base_dir / f"worker_{worker_id}"

        script_content = create_sbatch_script(
            midi_files=midi_files,
            output_dir=output_dir,
            job_name=job_name,
            BLENDER_PATH=args.blender_path,
        )

        # Submit the job
        result = submit_job(script_content, job_name)
        print(f"Submitted job for worker {worker_id} -> {output_dir}")
        print(f"Job submission result: {result}")


if __name__ == "__main__":
    main()
