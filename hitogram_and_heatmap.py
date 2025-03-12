import os
import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

def plot_run_analysis(on_off_dir, np_value, run_value, output_dir):
    #makes histogram of phis for a given run

    file_name = f"TF_on_off_Matrix_Np_{np_value}_run_{run_value}.json"
    file_path = os.path.join(on_off_dir, file_name)
    
    if not os.path.exists(file_path):
        print(f"File {file_name} not found in {on_off_dir}")
        return
    
    # Load the on/off binding matrix
    with open(file_path, 'r') as f:
        on_off_matrix = json.load(f)
    
    #use df to simplify process
    df = pd.DataFrame.from_dict(on_off_matrix, orient='index')
    df = df.sort_index()
    
    #Compute Phis
    phi_values = df.mean(axis=1)
    
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    #Plot Histogram of Phi values
    plt.figure(figsize=(8, 6))
    sns.histplot(phi_values, bins=20, kde=True, color='blue', edgecolor='black')
    plt.xlabel("Phi (Activity)")
    plt.ylabel("Count")
    plt.title(f"Histogram of Phi Values for Np={np_value}, Run={run_value}")
    plt.grid(True)
    hist_path = os.path.join(output_dir, f"phi_histogram_Np_{np_value}_run_{run_value}.png")
    plt.savefig(hist_path)
    print(f"Saved histogram as {hist_path}")
    plt.show()
    
    # Plot Heatmap of binding events over time
    plt.figure(figsize=(10, 6))
    sns.heatmap(df, cmap="coolwarm", cbar=True, xticklabels=50, yticklabels=10)
    plt.xlabel("Time Steps")
    plt.ylabel("Transcription Units (TUs)")
    plt.title(f"Heatmap of TU Binding Over Time (Np={np_value}, Run={run_value})")
    heatmap_path = os.path.join(output_dir, f"heatmap_Np_{np_value}_run_{run_value}.png")
    plt.savefig(heatmap_path)
    print(f"Saved heatmap as {heatmap_path}")
    plt.show()

if __name__ == "__main__":
    on_off_dir = "TF_On_Off_Matrices"  
    output_dir = os.path.dirname(os.path.abspath(__file__))  
    np_value = int(input("Enter Np value: "))  
    run_value = int(input("Enter run number: ")) 
    plot_run_analysis(on_off_dir, np_value, run_value, output_dir)
