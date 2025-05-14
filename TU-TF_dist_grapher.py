import numpy as np
import sys
import re
import json
import matplotlib.pyplot as plt

def parse_lammpstrj(file_path):

    with open(file_path, 'r') as f:
        lines = f.readlines()
    
    timestep_data = {}  
    timestep = None
    reading_atoms = False
    
    for i, line in enumerate(lines):
        if "ITEM: TIMESTEP" in line:
            timestep = int(lines[i + 1].strip())
            timestep_data[timestep] = []
            reading_atoms = False
        
        if "ITEM: ATOMS" in line:
            reading_atoms = True
            continue
        
        if reading_atoms:
            parts = line.strip().split()
            if len(parts) < 5:
                continue  # Skip lines that do not contain complete data
            bead_id, bead_type = int(parts[0]), int(parts[1])
            x, y, z = map(float, parts[2:5])
            timestep_data[timestep].append((bead_id, bead_type, x, y, z))
    
    return timestep_data

def plot_tu_tf_distances(file_path):
    # Parse trajectory file
    timestep_data = parse_lammpstrj(file_path)
    
    tu_tf_distances_over_time = []

    for timestep, beads in timestep_data.items():
        tu_positions = [np.array(b[2:]) for b in beads if b[1] == 2]  # TUs (type 2)
        tf_positions = [np.array(b[2:]) for b in beads if b[1] == 3]  # TFs (type 3)

        #Compute min distances 
        for tu_pos in tu_positions:
            if tf_positions:  # Avoid errors if no TFs are present
                min_distance = min(np.linalg.norm(tu_pos - tf_pos) for tf_pos in tf_positions)
                tu_tf_distances_over_time.append((timestep, min_distance))

    tu_tf_distances_over_time = np.array(tu_tf_distances_over_time)

  
    plt.figure(figsize=(10, 5))
    plt.scatter(tu_tf_distances_over_time[:, 0], tu_tf_distances_over_time[:, 1], alpha=0.5, s=5)
    plt.axhline(y=3.5, color='r', linestyle='--', label="Binding Threshold (3.5)")
    plt.xlabel("Timestep")
    plt.ylabel("Distance to Nearest TF")
    plt.title(f"TU-TF Minimum Distances Over Time ({file_path})")
    plt.legend()
    plt.grid()


    output_filename = f"TU_TF_distances_{file_path.split('/')[-1].replace('.lammpstrj', '.png')}"
    plt.savefig(output_filename)
    print(f"Plot saved as {output_filename}")

   

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python plot_tu_tf_distances.py <trajectory_file>")
        sys.exit(1)

    traj_file = sys.argv[1]
    plot_tu_tf_distances(traj_file)