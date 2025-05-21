#!/bin/bash
#SBATCH --job-name="piano_video_renders"
#SBATCH --nodes=1
#SBATCH --cpus-per-task=1
#SBATCH --gres=gpu:1,VRAM:8
#SBATCH --mem=16G
#SBATCH --time=180:00:00
#SBATCH --mail-type=ALL
#SBATCH --output=/storage/user/gruener/slurm/logs/slurm-%j.out
#SBATCH --error=/storage/user/gruener/slurm/logs/slurm-%j.out
pwd; hostname; date
nvidia-smi


PYTHONPATH=/home/stud/gruener/repos/piano-videos-dataset:$PYTHONPATH \\ 
/home/stud/gruener/blender-4.4.3-linux-x64/blender --python-use-system-env -b --python render.py -- -m data/bach-1.mid -o generated_data