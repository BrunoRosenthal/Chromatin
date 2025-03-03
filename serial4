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

# Loop over protein counts
for nprots in $(seq $n_min 10 $n_max); do
    run=1  # Initialize run counter
    runProt=1 # Initialise the run counter for in file
    echo "Generating input file for nprots=$nprots"
    
    # Call lammps_init.sh to generate input files for each configuration
    ./lammps_init.sh $nsites $sep $nprots $run "$traj_dir"  
    
    # Determine the generated directory name
    sim_dir=$(ls -d "$traj_dir/noise_Ns_${nsites}_l_${sep}_Np_${nprots}_run_${runProt}" 2>/dev/null | head -n 1)
    
    if [[ -z "$sim_dir" ]]; then
        echo "Error: Simulation directory for nprots=$nprots was not found!"
        exit 1
    fi
    
    # Loop over the number of runs
    for (( i=0; i<n_runs; i++ )); do
        echo "Running simulation for nprots=$nprots, run=$run"
        
        # Build the run script path
        run_script="${sim_dir}/run_noise_Ns_${nsites}_l_${sep}_Np_${nprots}_run_${run}.sh"
        
        if [[ ! -f "$run_script" ]]; then
            echo "Error: Run script $run_script not found!"
            exit 1
        fi
        
        chmod +x "$run_script"  # Ensure the script is executable
        echo "Running $run_script"
        "$run_script"  # Run the simulation
        
        # Modify the trajectory file name to avoid clashes
        traj_file="${sim_dir}/pos-equil_noise_Ns_${nsites}_l_${sep}_Np_${nprots}_run_${run}.lammpstrj"
        new_traj_file="${traj_dir}/pos-equil_noise_Ns_${nsites}_l_${sep}_Np_${nprots}_run_${run}_iter_${i}.lammpstrj"

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

        # Copy trajectory file with a new name to avoid clashes
        cp "$traj_file" "$new_traj_file"
        
        echo "Copied trajectory file to $new_traj_file"
        
        ((run++))  # Increment run number
    done
    ((runProt++))
done

echo "All simulations completed. Trajectory files saved in $traj_dir."
