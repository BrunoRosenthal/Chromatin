#!/bin/bash

TRAJ_DIR="/Users/bruno/Desktop/diss/src/completeTraj"  # Folder containing all trajectory files
SCRIPT="parseTraj.py"  # Python script to run

for traj_file in "$TRAJ_DIR"/*.lammpstrj; do
    echo "Processing $traj_file..."
    python "$SCRIPT" "$traj_file"
done

echo "All trajectory files processed!"
c