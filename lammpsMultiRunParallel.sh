#!/bin/bash
# lammps_batch_run.sh
# This script automates multiple runs of LAMMPS simulations with varying protein counts
# Runs are parallelized using GNU parallel

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

# Function to run each simulation
generate_and_run() {
    local nprots=$1
    local run=$2
    
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
}

# Export function for parallel execution
export -f generate_and_run
export nsites sep out_dir

# Generate parameter combinations and run in parallel
echo "Parallelizing simulations..."
seq $n_min 10 $n_max | while read nprots; do
    seq 1 $n_runs | while read run; do
        echo "$nprots $run"
    done
done | parallel -j $(nproc) --colsep ' ' generate_and_run
