import os
import numpy as np
import pandas as pd
from pathlib import Path

# Parameters
LENGTH_REPEAT_MAP = {
    10: 30,
    20: 30,
    40: 30,
    80: 10,
    100: 10
}

BINDING_THRESHOLD = 3.5
SIGMA = 1.0
BOX_SIZE = 100.0

# Function to parse trajectory file and compute phi per TU
def parse_traj(filepath, box_size=BOX_SIZE, sigma=SIGMA, binding_threshold=BINDING_THRESHOLD):
    try:
        with open(filepath, 'r') as f:
            lines = f.readlines()

        frames, i = [], 0
        while i < len(lines):
            if "ITEM: TIMESTEP" not in lines[i]:
                i += 1
                continue
            try:
                n_atoms = int(lines[i + 3])
                atom_lines = lines[i + 9:i + 9 + n_atoms]
                if len(atom_lines) != n_atoms:
                    i += 9 + n_atoms
                    continue
                frame = [list(map(float, ln.strip().split())) for ln in atom_lines]
                frames.append(frame)
                i += 9 + n_atoms
            except Exception:
                i += 1

        if not frames:
            return None

        arr0 = np.array(frames[0])
        types = arr0[:, 1].astype(int)
        tu_idx = np.where(types == 2)[0]
        tf_idx = np.where(types == 3)[0]

        if len(tu_idx) == 0 or len(tf_idx) == 0:
            return None

        tu_binding = []
        for frame in frames:
            arr = np.array(frame)
            coords = arr[:, 2:5] * box_size
            tu_coords = coords[tu_idx]
            tf_coords = coords[tf_idx]  # all TF beads

            bound = [
                1 if np.any(np.linalg.norm(tf_coords - tu, axis=1) <= binding_threshold * sigma) else 0
                for tu in tu_coords
            ]
            tu_binding.append(bound)

        tu_binding = np.array(tu_binding).T  # shape: [num_tus, num_timesteps]
        phi_vals = tu_binding.mean(axis=1)   # fraction of time each TU is bound
        return phi_vals

    except Exception:
        return None

# Run parser and generate CSVs for all spacings
def main():
    for l_val, n_repeats in LENGTH_REPEAT_MAP.items():
        base = Path(f"./runSep{l_val}")
        if not base.exists():
            print(f"⚠️ Directory not found: runSep{l_val}")
            continue

        results = []
        for n_tf in range(10, 101, 10):
            for run in range(1, n_repeats + 1):
                fname = f"pos_noise_Ns_30_l_{l_val}_Np_{n_tf}_run_{run}.lammpstrj"
                for file in base.rglob(fname):
                    phi = parse_traj(file)
                    if phi is not None:
                        results.append({
                            "TFs": n_tf,
                            "Run": run,
                            "phi_mean": round(np.mean(phi), 6),
                            "phi_std": round(np.std(phi), 6),
                            "File": file.name
                        })

        df = pd.DataFrame(results)
        out_file = f"phi_stats_l{l_val}_r{n_repeats}.csv"
        df.to_csv(out_file, index=False)
        print(f"✓ Saved: {out_file} with {len(df)} entries")

if __name__ == "__main__":
    main()
