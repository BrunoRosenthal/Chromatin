#!/bin/bash
# lammps_batch_run.sh
# This script automates multiple runs of LAMMPS simulations with varying protein counts

# Ensure we have the required arguments
if (( $# != 6 )); then
    echo "Usage: lammps_batch_run.sh nsites sep n_min n_max n_runs out_dir"
    exit 1
fi

nsites=$1     # Number of transcription units (TUs)
sep=$2        # Linear separation between TUs (in beads)
n_min=$3      # Minimum number of proteins (e.g., 10)
n_max=$4      # Maximum number of proteins (e.g., 100)
n_runs=$5     # Number of repetitions per protein count
out_dir=$6    # Output directory

# Loop over the number of proteins
for (( nprots=n_min; nprots<=n_max; nprots+=10 )); do
    for (( run=1; run<=n_runs; run++ )); do
        echo "Generating and running simulation for nprots=$nprots, run=$run"
        
        # Generate input files
        ./lammps_init.sh $nsites $sep $nprots $run $out_dir
        
        # Run the simulation
        run_script="$out_dir/noise_Ns_${nsites}_l_${sep}_Np_${nprots}_run_${run}/run_noise_Ns_${nsites}_l_${sep}_Np_${nprots}_run_${run}.sh"
        if [[ -f $run_script ]]; then
            bash $run_script
        else
            echo "Error: Run script $run_script not found!"
        fi
    done
done
