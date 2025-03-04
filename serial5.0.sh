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


#looping over protein counts
for nprots in $(seq $n_min 10 $n_max); do
    #looping for multiple runs at protein count
    for (( run=1; run<=n_runs; run++ )); do
        echo "Generating input file for nprots=$nprots, run=$run"
        
        # Ensure lammps_init.sh is executable before running it
        chmod +x lammps_init.sh
        ./lammps_init.sh $nsites $sep $nprots $run "$out_dir"  


        sim_dir=$(ls -d "$out_dir/noise_Ns_${nsites}_l_${sep}_Np_${nprots}_run_${run}" 2>/dev/null | head -n 1)

        # Check if the directory was found
        if [[ -z "$sim_dir" ]]; then
            echo "Error: Expected directory does not exist:"
            echo "  $out_dir/noise_Ns_${nsites}_l_${sep}_Np_${nprots}_run_${run}"
            exit 1  # Exit the script with an error status
        fi

        cd "$sim_dir"

        echo "Running the simulation for nprots=$nprots, run=$run"
        
        # Define the script filename
        script_name="run_noise_Ns_${nsites}_l_${sep}_Np_${nprots}_run_${run}.sh"

        # Ensure the script exists before making it executable
        if [[ ! -f "$script_name" ]]; then
            echo "Error: Script '$script_name' does not exist."
            exit 1
        fi

        chmod +x "$script_name"
        ./"$script_name"

        cd "$original_dir"

    done
done

echo "All simulations completed. Trajectory files saved in $out_dir."

        
