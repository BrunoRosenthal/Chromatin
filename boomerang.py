import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.optimize import curve_fit

def fit_function(x, a, b, c):
    #fit to quadratic function for later
    return a * x**2 + b * x + c

def plot_phi_statistics(csv_file, output_plot):
  #reads from csv from parse_mean_std.py  
  df = pd.read_csv(csv_file)
    
    #kill none values
    df = df.dropna()

  #diff colours for runs of same Np
    plt.figure(figsize=(8, 6))
    sns.scatterplot(
        data=df,
        x="Mean",
        y="Standard Deviation",
        hue="Np",
        palette="coolwarm",
        edgecolor='black',
        alpha=0.8
    )
    
    # Curve fitting ASSUMING QUADRATIC FROM PRE PRINT
    x_data = df["Mean"].values
    y_data = df["Standard Deviation"].values
    
    try:
        popt, _ = curve_fit(fit_function, x_data, y_data)
        x_fit = np.linspace(min(x_data), max(x_data), 100)
        y_fit = fit_function(x_fit, *popt)
        plt.plot(x_fit, y_fit, 'k--', label='Best Fit Curve')
    except Exception as e:
        print(f"Curve fitting failed: {e}")
    

    plt.xlabel("Mean Phi (Activity)")
    plt.ylabel("Standard Deviation of Phi (Noise)")
    plt.title("Boomerang Plot: Transcriptional Activity vs Noise")
    plt.legend(title="Number of TFs (Np)", loc='upper right')
    plt.grid(True)
    
    plt.savefig(output_plot)
    print(f"Saved plot as {output_plot}")
    plt.show()

if __name__ == "__main__":
    csv_file = "phi_statistics.csv"  
    output_plot = "boomerang.png"  
    plot_phi_statistics(csv_file, output_plot)
