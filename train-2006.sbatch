#!/bin/bash
#SBATCH --job-name="2006_renders"
#SBATCH --nodes=1
#SBATCH --cpus-per-task=4
#SBATCH --gres=gpu:1,VRAM:8
#SBATCH --mem=16G
#SBATCH --time=180:00:00
#SBATCH --mail-type=ALL
#SBATCH --output=/storage/user/wfel/slurm/logs/slurm-%j.out
#SBATCH --error=/storage/user/wfel/slurm/logs/slurm-%j.out
#SBATCH --nodelist=node11,node12,node13,node14,node15,node16,node17,node18,node19
pwd; hostname; date
nvidia-smi


PYTHONPATH=/home/stud/wfel/repos/piano-videos-dataset:$PYTHONPATH \
/home/stud/wfel/blender-4.4.3-linux-x64/blender \
  --python-use-system-env \
  -b \
  --python midi_to_piano/render.py \
  -- \
  -m /home/stud/wfel/repos/piano-videos-dataset/data/maestro-v3.0.0/2006 \
  -o generated_data