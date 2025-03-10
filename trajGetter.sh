#!/bin/bash

# Check for correct number of arguments
if (( $# != 7 )); then
    echo "Usage: lammps_traj_find nsites sep n_min n_max n_runs traj_dir target_dir"
    exit 1
fi

# Assign arguments to variables
nsites=$1     # Number of transcription units (TUs)
sep=$2        # Linear separation between TUs (in beads)
n_min=$3      # Minimum number of proteins (e.g., 10)
n_max=$4      # Maximum number of proteins (e.g., 100)
n_runs=$5     # Number of repetitions per protein count
out_dir=$6    # Directory containing simulation output
target_dir=$7 # Directory where copied files should be stored

# Ensure the target directory exists
mkdir -p "$target_dir"

original_dir=$(pwd)

# Loop through protein counts
for nprots in $(seq $n_min 10 $n_max); do
    # Loop through runs
    for (( run=1; run<=n_runs; run++ )); do
        sim_dir="$out_dir/noise_Ns_${nsites}_l_${sep}_Np_${nprots}_run_${run}"

        # Check if the directory exists
        if [[ ! -d "$sim_dir" ]]; then
            echo "Error: Expected directory does not exist:"
            echo "  $sim_dir"
            continue  # Skip this run instead of exiting
        fi

        # Try to change to the simulation directory
        if ! cd "$sim_dir"; then
            echo "Error: Could not enter directory '$sim_dir'"
            continue
        fi

        # Define the script filename
        script_name="pos_noise_Ns_${nsites}_l_${sep}_Np_${nprots}_run_${run}.lammpstrj"

        # Check if the file exists before copying
        if [[ -f "$script_name" ]]; then
            cp "$script_name" "$target_dir/"
            echo "Copied $script_name to $target_dir/"
        else
            echo "Warning: File not found: $script_name"
        fi

        # Return to original directory
        cd "$original_dir"
    done
done
