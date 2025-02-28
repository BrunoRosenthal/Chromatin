#!/bin/bash

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

# Store the current directory to return to it after each run
original_dir=$(pwd)

# Loop over protein counts
for nprots in $(seq $n_min 10 $n_max); do
    run=1  
    runProt=1 
    echo "Generating input file for nprots=$nprots"
    
    # Run init script for given protein count and run number 
    chmod +x lammps_init.sh  
    ./lammps_init.sh $nsites $sep $nprots $run "$traj_dir"  

    # Dynamically build the sim_dir based on the provided argument (traj_dir)
    sim_dir="${traj_dir}/noise_Ns_${nsites}_l_${sep}_Np_${nprots}_run_${runProt}"
    
    # Loop over the number of runs
    for (( i=0; i<n_runs; i++ )); do
        echo "Running simulation for nprots=$nprots, run=$run at address"
        
        # Change to the sim_dir where the simulation script is
        cd "$sim_dir"
        
        # Run the simulation and allow it to complete
        chmod +x run_noise_Ns_${nsites}_l_${sep}_Np_${nprots}_run_${run}.sh  
        ./run_noise_Ns_${nsites}_l_${sep}_Np_${nprots}_run_${run}.sh

        # Return to the original directory after the simulation
        cd "$original_dir"
        
        # Correctly look for the trajectory file based on the expected naming convention
        traj_file="${sim_dir}/pos-equil_noise_Ns_${nsites}_l_${sep}_Np_${nprots}_run_${run}.lammpstrj"
        
        # Copy the trajectory file to the designated directory
        cp "$traj_file" "$traj_dir/"
        
        ((run++))  # Increment run number
    done
    ((runProt++))
done
echo "All simulations completed. Trajectory files saved in $traj_dir."
