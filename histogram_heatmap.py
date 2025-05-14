import os
import json
import sys
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

def plot_run_analysis(on_off_dir, phi_dir, np_value, run_value, output_dir):
    """Generates a histogram of Phi values and a heatmap for a specific run."""
    
    # Construct file paths
    on_off_file = os.path.join(on_off_dir, f"TF_on_off_Matrix_Np_{np_value}_run_{run_value}.json")
    phi_file = os.path.join(phi_dir, f"TF_phis_Np_{np_value}_run_{run_value}.json")

    # Ensure files exist
    if not os.path.exists(on_off_file):
        print(f"[ERROR] On/Off matrix file {on_off_file} not found in {on_off_dir}")
        return

    # Load the on/off binding matrix
    with open(on_off_file, 'r') as f:
        on_off_matrix = json.load(f)

    # Convert to DataFrame
    df = pd.DataFrame.from_dict(on_off_matrix, orient='index').sort_index()

    # Try to load Phi values from JSON, otherwise compute from matrix
    if os.path.exists(phi_file):
        with open(phi_file, 'r') as f:
            phi_values = json.load(f)  # Load {TU: Phi} dictionary
        phi_values = pd.Series(phi_values)  # Convert to Pandas Series
        print(f"[INFO] Loaded Phi values from {phi_file}")
    else:
        print(f"[WARNING] Phi values file {phi_file} not found. Recomputing from On/Off matrix.")
        phi_values = df.mean(axis=1)

    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)

    # Plot Histogram of Phi values
    plt.figure(figsize=(8, 6))
    sns.histplot(phi_values, bins=20, kde=True, color='blue', edgecolor='black')
    plt.xlabel("Phi (Activity)")
    plt.ylabel("Count")
    plt.title(f"Histogram of Phi Values for Np={np_value}, Run={run_value}")
    plt.grid(True)
    hist_path = os.path.join(output_dir, f"phi_histogram_Np_{np_value}_run_{run_value}.png")
    plt.savefig(hist_path)
    print(f"[INFO] Saved histogram as {hist_path}")

    # Plot Heatmap of binding events over time
    plt.figure(figsize=(10, 6))
    sns.heatmap(df, cmap="coolwarm", cbar=True, xticklabels=50, yticklabels=10)
    plt.xlabel("Time Steps")
    plt.ylabel("Transcription Units (TUs)")
    plt.title(f"Heatmap of TU Binding Over Time (Np={np_value}, Run={run_value})")
    heatmap_path = os.path.join(output_dir, f"heatmap_Np_{np_value}_run_{run_value}.png")
    plt.savefig(heatmap_path)
    print(f"[INFO] Saved heatmap as {heatmap_path}")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python plot_run_analysis.py <Np_value> <run_number>")
        sys.exit(1)

    np_value = int(sys.argv[1])
    run_value = int(sys.argv[2])

    on_off_dir = "TF_On_Off_Matrices"  # Directory containing on/off matrices
    phi_dir = "TF_Phi_Values"  # Directory containing Phi JSONs
    output_dir = os.path.dirname(os.path.abspath(__file__))  # Save in the same directory as the script

    plot_run_analysis(on_off_dir, phi_dir, np_value, run_value, output_dir)
