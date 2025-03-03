#!/bin/bash
# lammps_batch_run.sh
# This script automates multiple runs of LAMMPS simulations with varying protein counts
# and saves only the trajectory files to a single directory.

# Ensure we have the required arguments
if (( $# != 6 )); then
    echo "Usage: lammps_batch_run.sh nsites sep n_min n_max n_runs traj_dir"
    exit 1
fi

nsites=$1     # Number of transcription units (TUs)
sep=$2        # Linear separation between TUs (in beads)
n_min=$3      # Minimum number of proteins (e.g., 10)
n_max=$4      # Maximum number of proteins (e.g., 100)
n_runs=$5     # Number of repetitions per protein count
traj_dir=$6   # Directory to store trajectory files

# Ensure trajectory directory exists
mkdir -p "$traj_dir"

# Loop over protein counts and runs
for nprots in $(seq $n_min 10 $n_max); do
    for (( run=1; run<=n_runs; run++ )); do
        echo "Generating input file for nprots=$nprots, run=$run"
        
        # Ensure lammps_init.sh is executable before running it
        chmod +x lammps_init.sh
        ./lammps_init.sh $nsites $sep $nprots $run "$traj_dir"  

        # Determine the simulation directory
        sim_dir=$(ls -d "$traj_dir/noise_Ns_${nsites}_l_${sep}_Np_${nprots}_run_${run}" 2>/dev/null | head -n 1)

        if [[ -z "$sim_dir" ]]; then
            echo "Error: Simulation directory for nprots=$nprots, run=$run was not found!"
            exit 1
        fi
        
        # Build the run script path
        run_script="${sim_dir}/run_noise_Ns_${nsites}_l_${sep}_Np_${nprots}_run_${run}.sh"
        
        if [[ ! -f "$run_script" ]]; then
            echo "Error: Run script $run_script not found!"
            exit 1
        fi
        
        chmod +x "$run_script"  # Ensure the run script is executable
        echo "Running $run_script"
        "$run_script"  # Run the simulation
        
        # Trajectory file path
        traj_file="${sim_dir}/pos-equil_noise_Ns_${nsites}_l_${sep}_Np_${nprots}_run_${run}.lammpstrj"
        new_traj_file="${traj_dir}/pos-equil_noise_Ns_${nsites}_l_${sep}_Np_${nprots}_run_${run}.lammpstrj"

        # Efficiently wait for the trajectory file to be created
        if command -v inotifywait &> /dev/null; then
            echo "Waiting for trajectory file to be generated..."
            inotifywait -q -e close_write "$sim_dir" --include "$(basename "$traj_file")"
        else
            while [[ ! -f "$traj_file" ]]; do
                echo "Waiting for trajectory file..."
                sleep 1  # Minimal delay for CPU efficiency
            done
        fi

        # Copy trajectory file to avoid overwriting
        cp "$traj_file" "$new_traj_file"
        
        echo "Copied trajectory file to $new_traj_file"
    done
done

echo "All simulations completed. Trajectory files saved in $traj_dir."
