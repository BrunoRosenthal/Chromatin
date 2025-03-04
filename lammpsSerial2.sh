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
    ./lammps_init.sh $nsites $sep $nprots $run "$traj_dir"  # Pass run number immediately before traj_dir
    
    # Determine the generated directory name (assuming consistent naming format)
    sim_dir=$(ls -d "$traj_dir/noise_Ns_${nsites}_l_${sep}_Np_${nprots}_run_${runProt}" 2>/dev/null | head -n 1)
    
    if [[ -z "$sim_dir" ]]; then
        echo "Error: Simulation directory for nprots=$nprots was not found!"
        exit 1
    fi
    
    # Loop over the number of runs
    for (( i=0; i<n_runs; i++ )); do
        echo "Running simulation for nprots=$nprots, run=$run"
        
        # Build the run script path (no extra slashes here)
        run_script="${sim_dir}/run_noise_Ns_${nsites}_l_${sep}_Np_${nprots}_run_${run}.sh"
        
        if [[ ! -f "$run_script" ]]; then
            echo "Error: Run script $run_script not found!"
            exit 1
        fi
        
        chmod +x "$run_script"  # Ensure the script is executable
        echo "Running $run_script"
        "$run_script"  # Run the simulation and allow output to be shown
        
        # Check if the trajectory file is generated and wait for completion
        traj_file="${sim_dir}/pos-equil_noise_Ns_${nsites}_l_${sep}_Np_${nprots}_run_${run}.lammpstrj"
        
        while [[ ! -f "$traj_file" ]]; do
            echo "Waiting for trajectory file to be generated..."
            sleep 5  # Wait 5 seconds before checking again
        done
        
        # Copy the trajectory file to the designated directory
        cp "$traj_file" "$traj_dir/"
        
        echo "Copied trajectory file for nprots=$nprots, run=$run"
        
        ((run++))  # Increment run number
    done
    ((runProt++))
done

echo "All simulations completed. Trajectory files saved in $traj_dir."
