#!/usr/bin/env python3
# create_dna_protein.py
# A simple script to generate a random walk polymer representing a
# coarse-grained DNA/chromatin fibre and protein beads in a box of size
# (lx,ly,lz). The centre of the box is at the origin and the first bead of the
# polymeris at point (x0,y0,z0) (or at the origin by default).

import sys
import numpy as np

args = sys.argv
nargs = len(args)

if (nargs != 9 and nargs != 12):
    print("Usage: create_dna_protein.py nbeads nprots sigma",
          "lx ly lz seed out_file [x0 y0 z0]")
    sys.exit(1)

nbeads = int(args.pop(1))  # Number of polymer beads
nprots = int(args.pop(1))  # Number of protein beads
sigma = float(args.pop(1)) # The bond length between beads (or bead size)
lx = float(args.pop(1))    # Box dimension in the x direction
ly = float(args.pop(1))    # Box dimension in the y direction
lz = float(args.pop(1))    # Box dimension in the z direction
seed = int(args.pop(1))    # Seed for the random generator
out_file = args.pop(1)     # Name of the output file

xhalf = lx/2.0
yhalf = ly/2.0
zhalf = lz/2.0

xprev = 0.0
yprev = 0.0
zprev = 0.0

# Define the bead type for DNA/chromatin and protein beads
dna_type = 1
protein_type = 2

# A helper function to check if the coordinates lie outside the box
def out_of_box(x,y,z):
    global xhalf, yhalf, zhalf
    return abs(x) > xhalf or abs(y) > yhalf or abs(z) > zhalf

# Set the initial bead of the polymer to the given coordinates (if supplied)
if (nargs == 12):
    x0 = float(args.pop(1))
    y0 = float(args.pop(1))
    z0 = float(args.pop(1))
    # Check that this point is within the simulation box
    if (out_of_box(x0,y0,z0)):
        print("Error: the initial point must be within the simulation box")
        sys.exit(1)
    xprev = x0
    yprev = y0
    zprev = z0

# Set up the random generator
rng = np.random.default_rng(seed)

with open(out_file,'w') as writer:
    # Output the position of the first polymer bead
    writer.write("{:d} {:d} {:f} {:f} {:f}\n".format(1,1,xprev,yprev,zprev))
    # Generate the positions of the remaining polymer beads
    for i in range(2,nbeads+1):
        while (True):
            # Generate a random position for the next bead to be anywhere on a
            # sphere of diameter sigma that is centred at the previous bead
            r = rng.random()
            costheta = 1.0-2.0*r
            sintheta = np.sqrt(1-costheta*costheta)
            r = rng.random()
            phi = 2.0*np.pi*r
            x = xprev+sigma*sintheta*np.cos(phi)
            y = yprev+sigma*sintheta*np.sin(phi)
            z = zprev+sigma*costheta

            # Make sure the new point is not outside the box, otherwise
            # re-generate it
            if (out_of_box(x,y,z)): continue
            
            writer.write("{:d} {:d} {:f} {:f} {:f}\n".format(i,dna_type,x,y,z))
            xprev = x
            yprev = y
            zprev = z
            break
    
    # Generate the positions of the protein beads
    for i in range(1,nprots+1):
        x = rng.random()*lx-xhalf
        y = rng.random()*ly-yhalf
        z = rng.random()*lz-zhalf
        writer.write("{:d} {:d} {:f} {:f} {:f}\n".format(
            i+nbeads,protein_type,x,y,z))
