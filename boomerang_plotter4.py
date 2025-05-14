import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.optimize import curve_fit

def boomerang_fit_function(mu, A_sigma, alpha, beta):
    return A_sigma * (mu ** alpha) * ((1 - mu) ** beta)

def plot_phi_statistics(csv_file, output_plot):
    df = pd.read_csv(csv_file)
    df = df.dropna()

    grouped_df = df.groupby("Np").agg({
        "Mean": "mean",
        "Standard Deviation": "mean"
    }).reset_index()

    # Wider figure for a balanced aesthetic layout
    plt.figure(figsize=(12, 6))

    sns.scatterplot(
        data=grouped_df,
        x="Mean",
        y="Standard Deviation",
        hue=grouped_df["Np"].astype(str),
        style=grouped_df["Np"].astype(str),
        palette="coolwarm",
        edgecolor='black',
        alpha=0.9,
        s=80
    )

    x_data = grouped_df["Mean"].values
    y_data = grouped_df["Standard Deviation"].values
    p0 = [0.2, 0.5, 0.5]

    try:
        popt, _ = curve_fit(boomerang_fit_function, x_data, y_data, p0=p0)
        x_fit = np.linspace(min(x_data), max(x_data), 100)
        y_fit = boomerang_fit_function(x_fit, *popt)
        # Legend label with multi-line formatting
        fit_label = f'Fit:\nA = {popt[0]:.3f}\nα = {popt[1]:.3f}\nβ = {popt[2]:.3f}'
        plt.plot(x_fit, y_fit, 'k--', label=fit_label)
    except Exception as e:
        print(f"Curve fitting failed: {e}")

    plt.xlabel("Mean Phi (Activity)")
    plt.ylabel("Standard Deviation of Phi (Noise)")
    plt.title("Boomerang Plot: Transcriptional Activity vs Noise (Averaged by Np)")

    plt.legend(
        title="Number of TFs (Np)",
        bbox_to_anchor=(1.02, 1),
        loc='upper left',
        borderaxespad=0.
    )

    plt.grid(True)
    plt.tight_layout(rect=[0, 0, 0.8, 1])  # Leave space on the right

    plt.savefig(output_plot, bbox_inches='tight')
    print(f"Saved plot as {output_plot}")
    plt.show()

if __name__ == "__main__":
    csv_file = "phi_statistics.csv"
    output_plot = "boomerang_averaged_fit.png"
    plot_phi_statistics(csv_file, output_plot)