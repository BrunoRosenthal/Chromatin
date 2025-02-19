#!/bin/bash
# lammps_init.sh
# A script to generate the LAMMPS script and init config file

# Make sure we are using python3
pyx=python3

####################

# Input arguments (key parameters for the simuation)

if (( $# != 5 )); then
    echo "Usage: lammps_init.sh nsites sep nprots run out_dir"
    exit 1
fi

nsites=$1     # Number of transcription units (TUs)
sep=$2        # Linear separation between TUs (in beads)
nprots=$3     # Number of protein beads  
run=$4        # Trial number
out_dir=$5    # Output directory

####################

# Variable definitions

# Required programs
init_py="create_polymer.py" # Python script for generating initial
                                # chromatin/protein config
lmp_exe="/usr/bin/lmp" # Path to LAMMPS executable

# Set the total number of chromatin beads, bonds, and angle bonds
npolys=$($pyx -c "print($sep*($nsites+1)-1)")
nbonds=$(($npolys-1))
nbondtypes=1
nangles=$(($npolys-2))
nbeads=$(($npolys+$nprots)) # Total number of beads including proteins

# Assign a name for the simulation run
name="noise_Ns_${nsites}_l_${sep}_Np_${nprots}_run_${run}"

# Create the output directory where the generated scripts/files will be stored
out_dir="${out_dir}/${name}"
if [[ ! -d $out_dir ]]; then
    mkdir -p $out_dir
fi

# Path to generated scripts and output files
dump_screen=1 # Whether to dump the screen output to file (*.slog) or not
run_sh="${out_dir}/run_${name}.sh"
traj_file="${out_dir}/traj_${name}.dat"
seed_file="${out_dir}/seed_${name}.dat"
slog_file="${out_dir}/${name}.slog"
log_file="${out_dir}/${name}.log"
init_file="${out_dir}/${name}.in"
out_file="${out_dir}/${name}.out"
lam_file="${out_dir}/${name}.lam"
restart_file="${out_dir}/${name}.restart"
pos_file="${out_dir}/pos_${name}.lammpstrj"
pos_equil_file="${out_dir}/pos-equil_${name}.lammpstrj"

####################

# Some helper functions

# Rescale epsilon such that the minimum of the truncated and shifted LJ
# potential actually reaches -epsilon
function rescale_energy() {
    local e=$1
    local rc=$2
    local s=$3
    echo $($pyx -c "
norm = 1.0+4.0*(($s/$rc)**12.0-($s/$rc)**6.0)
print($e/norm if norm > 0.0 else $e)")
}

# Convert from simulation time unit to timesteps
function get_timestep() {
    local tau=$1
    local dt=$2
    echo $($pyx -c "print(int($tau/$dt))")
}

# Generate random seeds
function get_rand(){
    # Generate a 4-byte random integer using urandom
    # Need to make sure the seed is positive and less than 900 million as
    # LAMMPS does not like seed values larger than this!
    # Only use the leftmost 29 bits of the integer (since 2^29 = 536870912)
    rand=$($pyx -c "print(($(od -vAn -N4 -tu4 < /dev/urandom) >> 3)+1)")
    echo $rand
}

####################

# 0. Generate the polymer

box_size=100.0 # Simulation box size
sigma=1.0 # Bead size

echo "Creating a polymer chain with $npolys beads"
echo "Using box size = $box_size sigma"

# Set the box boundaries
lo=$($pyx -c "print(-int(${box_size}/2.0))")
hi=$($pyx -c "print(int(${box_size}/2.0))")

seed_init_poly=$(get_rand)
echo "Init polymer seed = ${seed_init_poly}" > $seed_file

$pyx $init_py $npolys $nprots $sigma $box_size $box_size $box_size \
     $seed_init_poly $traj_file

####################

# 1. Create LAMMPS bead file

echo "Creating the LAMMPS input config file ..."

echo "LAMMPS data file via

${nbeads} atoms
4 atom types
${nbonds} bonds
${nbondtypes} bond types
${nangles} angles
1 angle types

${lo} ${hi} xlo xhi
${lo} ${hi} ylo yhi
${lo} ${hi} zlo zhi

Masses

1 1
2 1
3 1
4 1

Atoms # angle
" > $init_file

# Add polymer and protein beads
nprots_half=$($pyx -c "
import numpy as np
rng = np.random.default_rng($seed_init_poly)
# Use a random generator to decide how to split the proteins into the ON and 
# OFF groups if the number of proteins is not an even number
if ($nprots % 2 == 1):
    if (rng.random() < 0.5):
        print(int(np.ceil($nprots/2)))
    else:
        print(int(np.floor($nprots/2)))
else:
    print(int($nprots/2))
")

awk -v l=$sep -v nb=$npolys -v nph=$nprots_half '{
if (NR <= nb) { # Chromatin beads
  nn = NR-l
  # Make sure the TUs are spaced out equally
  if (nn >= 0 && nn % l == 0) {
    btype = 2 # TU chromatin beads
  } else {
    btype = 1 # non-TU chromatin beads
  }
} else if (NR <= nb+nph) { # ON protein beads
  btype = 3
} else { # OFF protein beads
  btype = 4
}
print NR,1,btype,$3,$4,$5,0,0,0
}' $traj_file >> $init_file
rm $traj_file

awk -v nb=$npolys -v nangles=$nangles 'BEGIN {
  print ""
  print "Bonds"
  print ""
  for (i=1;i<=nb-1;i++) {print i,1,i,i+1}
  print ""
  print "Angles"
  print ""
  for (i=1;i<=nangles;i++) {print i,1,i,i+1,i+2}
}' >> $init_file

####################

# 2. Create the LAMMPS driver script

echo "Creating the LAMMPS driver script ..."

# Parameters for the potentials

# Default cutoff distance
rc_0=1.122462048309373

# LJ potential
rc=1.8
elow=3.0
ehigh=7.0

# FENE bond
K_f=30.0
R_0=1.6

# Angle bond
l_p=3.0 # Persistence length

# Rescale the energy so that the potential depth reaches -epsilon
elow=$(rescale_energy $elow $rc $sigma)
ehigh=$(rescale_energy $ehigh $rc $sigma)

# Simulation run times (in simulation time unit)
dt=0.01 # Size of each timestep
run_init_time_1=100   # Equilibration with harmonic bonds
run_init_time_2=10000 # Equilibration with FENE bonds
run_loop_time=100     # Run time between protein switching events
switch_time=100000    # Protein switching time
nloops=1100           # Number of protein switching events

# Dump frequencies (in simulation time unit)
thermo_equil_printfreq=1000
dump_equil_printfreq=1000
thermo_printfreq=1000
dump_printfreq=1000

# Convert run times and dump frequencies to be in timesteps
run_init_time_1=$(get_timestep $run_init_time_1 $dt)
run_init_time_2=$(get_timestep $run_init_time_2 $dt)
run_loop_time=$(get_timestep $run_loop_time $dt)
switch_time=$(get_timestep $switch_time $dt)
dump_equil_printfreq=$(get_timestep $dump_equil_printfreq $dt)
dump_printfreq=$(get_timestep $dump_printfreq $dt)
thermo_printfreq=$(get_timestep $thermo_printfreq $dt)

# Convert protein switching time into a switching probability
switch_prob=$($pyx -c "print($run_loop_time/float($switch_time))")

# Seeds for random generators
seed_langevin_equil=$(get_rand)
seed_langevin_main=$(get_rand)
seed_switch_on=$(get_rand)
seed_switch_off=$(get_rand)
echo "Langevin equil seed = ${seed_langevin_equil}" >> $seed_file
echo "Langevin main seed = ${seed_langevin_main}" >> $seed_file
echo "Protein switch on seed = ${seed_switch_on}" >> $seed_file
echo "Protein switch off seed = ${seed_switch_off}" >> $seed_file

# If in doubt with any of the commands, revisit the LAMMPS tutorials and/or
# consult LAMMPS documentation

echo "
##################################################

# Simulation basic setup

units lj
atom_style angle
boundary p p p

neighbor 1.9 bin
neigh_modify every 1 delay 1 check yes

comm_style tiled
comm_modify mode single cutoff 4.0 vel yes

read_data $(basename $init_file)

##################################################

# Define groups
# There are four types of beads:
# 1 = Non-TU chromatin beads
# 2 = TU chromatin beads
# 3 = ON protein beads
# 4 = OFF protein beads

group all type 1 2 3 4
group poly type 1 2 # Chromatin beads
group prot type 3 4 # Protein beads

##################################################

# Dumps

compute gyr poly gyration
thermo ${thermo_printfreq}
thermo_style custom step temp epair c_gyr
dump 1 all custom ${dump_equil_printfreq} $(basename $pos_equil_file) &
id type xs ys zs ix iy iz

##################################################

# Potentials

bond_style harmonic
bond_coeff 1 100.0 1.1

angle_style cosine
angle_coeff 1 10.0 # Stiff fibre to remove overlap

pair_style soft ${rc_0}
pair_coeff * * 100.0 ${rc_0}

##################################################

# Set integrator/dynamics

fix 1 all nve
fix 2 all langevin 1.0 1.0 1.0 ${seed_langevin_equil}

##################################################

# Initial equilibration

timestep ${dt}
run ${run_init_time_1}

##################################################

# Equilibrate with FENE bonds

bond_style fene
special_bonds fene
bond_coeff 1 ${K_f} ${R_0} 1.0 ${sigma}

angle_coeff 1 ${l_p}

pair_style lj/cut ${rc_0}
pair_coeff * * 1.0 ${sigma} ${rc_0}

run ${run_init_time_2}

##################################################

# Clear all fixes and dumps before the main simulation

unfix 1
unfix 2
undump 1

##################################################

# Main simulation

# Set all pairwise interactions to be purely repulsive except:
# A weak, non-specific attractive interaction between non-TU beads and proteins
# A strong, specific attractive interaction between TU beads and proteins

pair_style lj/cut ${rc_0}
pair_coeff * * 1.0 ${sigma} ${rc_0}
pair_coeff 1 3 ${elow} ${sigma} ${rc}
pair_coeff 2 3 ${ehigh} ${sigma} ${rc}

# Reset the integrator/dynamics

fix 1 all nve
fix 2 all langevin 1.0 1.0 1.0 ${seed_langevin_main}

# Dumps

dump 1 all custom ${dump_printfreq} $(basename $pos_file) &
id type xs ys zs ix iy iz

# Reset time and run the main simulation, which is done in a loop. Protein
# switching (ON <-> OFF) is done between each loop period

reset_timestep 0

variable colourstep loop ${nloops}
label switchloop

run ${run_loop_time} post no

# Do protein switching

variable seed_on equal (${seed_switch_on}+\${colourstep})
variable seed_off equal (${seed_switch_off}+\${colourstep})

group prot_on type 3
group prot_off type 4

set group prot_on type/fraction 4 ${switch_prob} \${seed_off}
set group prot_off type/fraction 3 ${switch_prob} \${seed_on}

group prot_on delete
group prot_off delete

next colourstep

jump $(basename $lam_file) switchloop

##################################################

# Clean up and output end result

unfix 1
unfix 2
undump 1

# Output a restart file that stores the full final configuration of the
# simulation in a binary format, in case we need to run the simulation for
# longer starting from this configuration

write_restart $(basename $restart_file)

# Output the final configuration of the system in a human readable format

write_data $(basename $out_file) nocoeff

##################################################
" > $lam_file

# Create a bash script that will run LAMMPS directly, so you can start the
# simulation by running this script, i.e.,
# bash ${run_sh}
if [[ $dump_screen == 1 ]]; then
    screen_opt=$(basename $slog_file)
else
    screen_opt="none"
fi
echo \
"#!/bin/bash
$lmp_exe -in $(basename $lam_file) -screen $screen_opt -log $(basename $log_file)
" > $run_sh
chmod +x $run_sh
