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
    sim_dir=$(ls -d noise_Ns_${nsites}_l_${sep}_Np_${nprots}_run_${runProt}/ 2>/dev/null | head -n 1)
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
        "$run_script" > /dev/null 2>&1  # Run the simulation and suppress output
        
        # Correctly look for the trajectory file based on the expected naming convention
        traj_file="${sim_dir}/traj_noise_Ns_${nsites}_l_${sep}_Np_${nprots}_run_${run}.dat"
        
        if [[ ! -f "$traj_file" ]]; then
            echo "Error: Trajectory file $traj_file not found!"
            exit 1
        fi
        
        # Move trajectory file to the designated directory
        mv "$traj_file" "$traj_dir/"
        
        ((run++))  # Increment run number
    done
((runProt++)
done

echo "All simulations completed. Trajectory files saved in $traj_dir."
