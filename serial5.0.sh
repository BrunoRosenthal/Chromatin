if (( $# != 6 )); then
    echo "Usage: lammps_batch_run.sh nsites sep n_min n_max n_runs traj_dir"
    exit 1
fi

nsites=$1     # Number of transcription units (TUs)
sep=$2        # Linear separation between TUs (in beads)
n_min=$3      # Minimum number of proteins (e.g., 10)
n_max=$4      # Maximum number of proteins (e.g., 100)
n_runs=$5     # Number of repetitions per protein count
out_dir=$6   # Directory to store trajectory files

original_dir=$(pwd)

# Looping over protein counts
for nprots in $(seq $n_min 10 $n_max); do
    # Looping for multiple runs at protein count
    for (( run=1; run<=n_runs; run++ )); do
        echo "Generating input file for nprots=$nprots, run=$run"
        
        # Ensure lammps_init.sh is executable before running it
        chmod +x lammps_init.sh
        ./lammps_init.sh $nsites $sep $nprots $run "$out_dir"

        # Define expected simulation directory
        sim_dir="$out_dir/noise_Ns_${nsites}_l_${sep}_Np_${nprots}_run_${run}"
        echo "Checking for directory: $sim_dir"

        # Check if the directory exists
        if [[ ! -d "$sim_dir" ]]; then
            echo "Error: Expected directory does not exist:"
            echo "  $sim_dir"
            continue  # Skip this run instead of exiting
        fi

        if ! cd "$sim_dir"; then
            echo "Error: Could not enter directory '$sim_dir'"
            continue
        fi

        echo "Running the simulation for nprots=$nprots, run=$run"

        # Define the script filename
        script_name="run_noise_Ns_${nsites}_l_${sep}_Np_${nprots}_run_${run}.sh"

        # Ensure the script exists before making it executable
        if [[ ! -f "$script_name" ]]; then
            echo "Error: Script '$script_name' does not exist."
            cd "$original_dir"
            continue
        fi

        chmod +x "$script_name"
        ./"$script_name"

        cd "$original_dir"

    done
done

echo "All simulations completed. Trajectory files saved in $out_dir."
