import numpy as np
import sys
import re
import json

def parse_lammpstrj(file_path, binding_threshold=3.5):
        #returns
        #on_off_matrix (dict): Keys are TU IDs, values are lists of 0s and 1s per timestep
        #phi_values (dict): Keys are TU IDs, values are Phi values (ratio of bound time)
  
    timestep_data = {}  
    timestep = None
    reading_atoms = False
    current_timestep_beads = []  

    # Read the LAMMPS trajectory file
    with open(file_path, 'r') as f:
        lines = f.readlines()
    
    for i, line in enumerate(lines):
        if "ITEM: TIMESTEP" in line:
            if timestep is not None and current_timestep_beads:
                timestep_data[timestep] = current_timestep_beads  
            timestep = int(lines[i + 1].strip())  
            current_timestep_beads = []
            reading_atoms = False
        
        if "ITEM: ATOMS" in line:
            reading_atoms = True
            continue
        
        if reading_atoms:
            parts = line.strip().split()
            bead_id, bead_type = int(parts[0]), int(parts[1])
            x, y, z = map(float, parts[2:5])
            current_timestep_beads.append((bead_id, bead_type, x, y, z))

    #ensure last timestep is stored
    if timestep is not None and current_timestep_beads:
        timestep_data[timestep] = current_timestep_beads

    total_timesteps = len(timestep_data) 
    tu_binding_states = {}  

    #Process each timestep
    for timestep, beads in sorted(timestep_data.items()):
        tu_positions = [(b[0], np.array(b[2:])) for b in beads if b[1] == 2]  # TUs (type 2)
        tf_positions = [np.array(b[2:]) for b in beads if b[1] == 3]  # TFs (type 3)

        for tu_id, tu_pos in tu_positions:
            if tu_id not in tu_binding_states:
                tu_binding_states[tu_id] = []  

            bound = any(np.linalg.norm(tu_pos - tf_pos) <= binding_threshold for tf_pos in tf_positions)
            tu_binding_states[tu_id].append(1 if bound else 0)  # Append binding state

    # Compute Phi values
    phi_values = {tu: sum(states) / total_timesteps for tu, states in tu_binding_states.items()}

    return tu_binding_states, phi_values

def extract_np_run(file_path):
    #gets Np (number of proteins) and run number from the traj file name
    match = re.search(r'Np_(\d+)_run_(\d+)', file_path)
    if match:
        return int(match.group(1)), int(match.group(2))
    else:
        raise ValueError("File name does not match expected format: Np_{Np}_run_{run}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python parse_lammpstrj.py <trajectory_file>")
        sys.exit(1)
    
    traj_file = sys.argv[1]
    np_value, run_value = extract_np_run(traj_file)
    on_off_matrix, phi_dict = parse_lammpstrj(traj_file)
    
    # Save On/Off Matrix
    on_off_file = f"TF_on_off_Matrix_Np_{np_value}_run_{run_value}.json"
    with open(on_off_file, 'w') as f:
        json.dump(on_off_matrix, f, indent=4)
    
    # Save Phi Values
    phi_file = f"TF_phis_Np_{np_value}_run_{run_value}.json"
    with open(phi_file, 'w') as f:
        json.dump(phi_dict, f, indent=4)
    
    print(f"Saved On/Off Matrix to {on_off_file}")
    print(f"Saved Phi Values to {phi_file}")
