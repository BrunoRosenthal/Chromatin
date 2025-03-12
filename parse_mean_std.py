import os
import json
import pandas as pd
import numpy as np
import re

def extract_np_run(file_name):
    #pulling phi values file for given run
    match = re.search(r'Np_(\d+)_run_(\d+)', file_name)
    if match:
        return int(match.group(1)), int(match.group(2))
    else:
        raise ValueError("File name does not match expected format: Np_{Np}_run_{run}")

def compute_phi_stats(phi_dir, output_csv):
    #iterating through all runs and Nps
    data_records = []
    
    for file_name in os.listdir(phi_dir):
        if file_name.endswith(".json"):
            file_path = os.path.join(phi_dir, file_name)
            
            try:
                np_value, run_value = extract_np_run(file_name)
            except ValueError as e:
                print(f"Skipping file {file_name}: {e}")
                continue
            
            with open(file_path, 'r') as f:
                phi_dict = json.load(f)
                phi_values = np.array(list(phi_dict.values()))
                
                if phi_values.size > 0:
                    mean_phi = np.mean(phi_values)
                    std_phi = np.std(phi_values, ddof=0)  
                else:
                    mean_phi = None
                    std_phi = None
                
                data_records.append([np_value, run_value, mean_phi, std_phi])
    
    #using df and save to CSV
    df = pd.DataFrame(data_records, columns=["Np", "Run", "Mean", "Standard Deviation"])
    df.to_csv(output_csv, index=False, mode='a', header=not os.path.exists(output_csv))
    
    print(f"Saved Phi statistics to {output_csv}")

if __name__ == "__main__":
    phi_values_dir = "TF_Phi_Values"  
    output_csv_file = "phi_statistics.csv"  
    compute_phi_stats(phi_values_dir, output_csv_file)
