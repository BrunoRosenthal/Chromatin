import numpy as np
import os
import json
import sys
import re

if len(sys.argv) != 2:
    print("Usage: python script.py <trajectory_filename>")
    sys.exit(1)

# Define directory paths
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))  
TRAJ_DIR = os.path.join(SCRIPT_DIR, "trajs")  
ON_OFF_DIR = os.path.join(SCRIPT_DIR, "TF_On_Off_Matrices")  
PHI_DIR = os.path.join(SCRIPT_DIR, "TF_Phi_Values")  

#make directories if not there
os.makedirs(ON_OFF_DIR, exist_ok=True)
os.makedirs(PHI_DIR, exist_ok=True)

traj_filename = sys.argv[1]
traj_file_path = os.path.join(TRAJ_DIR, traj_filename)

if not os.path.exists(traj_file_path):
    print(f"Error: File '{traj_filename}' not found in '{TRAJ_DIR}'")
    sys.exit(1)

#find right file using generic form 
match = re.search(r'Np_(\d+)_run_(\d+)', traj_filename)
if match:
    np_value, run_value = int(match.group(1)), int(match.group(2))
else:
    print("Error: Could not extract Np and run number from filename.")
    sys.exit(1)

#parseing traj file w real distance 
def parse_lammpstrj_with_box(file_path, binding_threshold=3.5):

    with open(file_path, 'r') as f:
        lines = f.readlines()
    
    timestep_data = {} 
    timestep = None
    reading_atoms = False
    box_bounds = {}  
    
    for i, line in enumerate(lines):
        if "ITEM: TIMESTEP" in line:
            timestep = int(lines[i + 1].strip())
            timestep_data[timestep] = []
            reading_atoms = False
        
        elif "ITEM: BOX BOUNDS" in line:
            #read the next three lines as x, y, z bounds
            box_bounds["x"] = list(map(float, lines[i + 1].strip().split()))
            box_bounds["y"] = list(map(float, lines[i + 2].strip().split()))
            box_bounds["z"] = list(map(float, lines[i + 3].strip().split()))

        elif "ITEM: ATOMS" in line:
            reading_atoms = True
            continue

        elif reading_atoms:
            parts = line.strip().split()
            if len(parts) < 5:
                continue  
            bead_id, bead_type = int(parts[0]), int(parts[1])
            x_scaled, y_scaled, z_scaled = map(float, parts[2:5])

            #getting real coords 
            x_real = x_scaled * (box_bounds["x"][1] - box_bounds["x"][0]) + box_bounds["x"][0]
            y_real = y_scaled * (box_bounds["y"][1] - box_bounds["y"][0]) + box_bounds["y"][0]
            z_real = z_scaled * (box_bounds["z"][1] - box_bounds["z"][0]) + box_bounds["z"][0]

            timestep_data[timestep].append((bead_id, bead_type, x_real, y_real, z_real))

    total_timesteps = len(timestep_data)
    tu_binding_states = {}  

    for timestep, beads in timestep_data.items():
        tu_positions = [(b[0], b[2:]) for b in beads if b[1] == 2]  # TUs (type 2)
        tf_positions = [b[2:] for b in beads if b[1] == 3]  # TFs (type 3)

        for tu_id, tu_pos in tu_positions:
            if tu_id not in tu_binding_states:
                tu_binding_states[tu_id] = []
            
            bound = any(np.linalg.norm(np.array(tu_pos) - np.array(tf_pos)) <= binding_threshold 
                        for tf_pos in tf_positions)

            tu_binding_states[tu_id].append(1 if bound else 0)

    # Compute Phi values
    phi_values = {tu: sum(states) / total_timesteps for tu, states in tu_binding_states.items()}

    return tu_binding_states, phi_values


on_off_matrix, phi_dict = parse_lammpstrj_with_box(traj_file_path, binding_threshold=3.5)

# save on off 
on_off_file = os.path.join(ON_OFF_DIR, f"TF_on_off_Matrix_Np_{np_value}_run_{run_value}.json")
with open(on_off_file, 'w') as f:
    json.dump(on_off_matrix, f, indent=4)

# save pgi values
phi_file = os.path.join(PHI_DIR, f"TF_phis_Np_{np_value}_run_{run_value}.json")
with open(phi_file, 'w') as f:
    json.dump(phi_dict, f, indent=4)

phi_csv_file = os.path.join(PHI_DIR, f"TF_phis_Np_{np_value}_run_{run_value}.csv")
with open(phi_csv_file, 'w') as f:
    f.write("TU,Phi\n")
    for tu, phi in phi_dict.items():
        f.write(f"{tu},{phi}\n")

print(f"Processed {traj_filename} and saved results to:")
print(f"- {on_off_file}")
print(f"- {phi_file}")
print(f"- {phi_csv_file}")
