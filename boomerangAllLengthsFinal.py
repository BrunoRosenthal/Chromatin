import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
from pathlib import Path

# Fitting model from the paper
def normalized_boomerang(mu, A_sigma, alpha, beta):
    nu = alpha / (alpha + beta)
    norm = (nu ** alpha) * ((1 - nu) ** beta)
    return A_sigma * (mu ** alpha) * ((1 - mu) ** beta) / norm

# Load CSVs for all l-values
paths = {
    10: "phi_stats_l10_r30.csv",
    20: "phi_stats_l20_r30.csv",
    30: "phi_statistics.csv",  # validated l=30
    40: "phi_stats_l40_r30.csv",
    80: "phi_stats_l80_r10.csv",
    100: "phi_stats_l100_r10.csv"
}

# Group φ values by TF and compute mean/std for plotting
grouped_by_l = {}
for l, path in paths.items():
    df = pd.read_csv(path)
    if l == 30:
        grouped = df.groupby("Np").agg({
            "Mean": "mean",
            "Standard Deviation": "mean"
        }).reset_index().rename(columns={"Np": "TFs", "Mean": "phi_mean", "Standard Deviation": "phi_std"})
    else:
        grouped = df.groupby("TFs").agg({
            "phi_mean": "mean",
            "phi_std": "mean"
        }).reset_index()
    grouped_by_l[l] = grouped

# Plotting setup
colors = plt.cm.plasma(np.linspace(0, 1, len(grouped_by_l)))
fit_params = {}
plt.figure(figsize=(7, 5))

# Fit and plot each l's data
def fit_and_plot(ax, mu_vals, sigma_vals, label, color):
    try:
        popt, _ = curve_fit(normalized_boomerang, mu_vals, sigma_vals, bounds=([0, 0, 0], [1, 10, 10]))
        mu_fit = np.linspace(0.01, 0.99, 300)
        sigma_fit = normalized_boomerang(mu_fit, *popt)
        ax.plot(mu_fit, sigma_fit, color=color, lw=2, label=label)
        return popt
    except RuntimeError:
        return None

fig, ax = plt.subplots(figsize=(7, 5))
for (l, df), color in zip(sorted(grouped_by_l.items()), colors):
    mu = df["phi_mean"].values
    sigma = df["phi_std"].values
    ax.scatter(mu, sigma, color=color, s=30)
    params = fit_and_plot(ax, mu, sigma, f"$d_{{\mathrm{{TU}}}} = {l}$", color)
    fit_params[l] = params

# Add binomial baseline
mu_bin = np.linspace(0.01, 0.99, 200)
sigma_bin = np.sqrt(mu_bin * (1 - mu_bin) / 101)
ax.plot(mu_bin, sigma_bin, 'k--', linewidth=1, label="Binomial")

# Final styling
ax.set_xlim(0, 1)
ax.set_ylim(0, 0.45)
ax.set_xlabel(r"$\mu(\phi)$")
ax.set_ylabel(r"$\sigma(\phi)$")
ax.set_title("Boomerang curves for different $d_{\mathrm{TU}}$")
ax.legend(title=r"$d_{\mathrm{TU}}$", fontsize=9)
plt.grid(True)
plt.tight_layout()
plt.savefig("boomerang_all_lengths_final.png", dpi=300)
plt.show()

# Save fitted parameters
fit_param_records = []
for l, popt in fit_params.items():
    if popt is not None:
        A_sigma, alpha, beta = popt
        nu = alpha / (alpha + beta)
        fit_param_records.append({
            "l (kbp)": l,
            "A_sigma (max \u03c3)": round(A_sigma, 4),
            "alpha": round(alpha, 4),
            "beta": round(beta, 4),
            "nu (\u03bc at max \u03c3)": round(nu, 4)
        })

df_fits = pd.DataFrame(fit_param_records).sort_values("l (kbp)")
df_fits.to_csv("boomerang_fit_parameters.csv", index=False)
