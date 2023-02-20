#!/bin/bash

#SBATCH --job-nam=augmentation

#SBATCH -p highmemdell

#SBATCH -c 20

#SBATCH --mail-user=billhappi@gmail.com

#SBATCH --mail-type=ALL 

rm -rf ./inputs/*

rm -rf ./outputs/*

scp -r /data3/projects/agrold ./inputs/

module load system/python/3.8.12

srun -p highmemdell --nodelist=node29 --pty nohup sh ./sub_job.sh &
