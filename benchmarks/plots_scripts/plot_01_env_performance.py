"""
Plot 1: Performance by Environment - SLM Latency and Throughput
"""

import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
from data_loader import BenchmarkLoader
from statistics import mean


def plot_env_performance(loader: BenchmarkLoader, output_dir: Path) -> None:
    """Creates chart of SLM latency and throughput by environment"""
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    summary = loader.summary_by_env_model()
    
    # Agrupa por environment
    env_data = {}
    for row in summary:
        env = row["environment"]
        if env not in env_data:
            env_data[env] = []
        env_data[env].append(row)
    
    # Figura com 2 subplots
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
    
    # Plot 1: SLM Latency by environment
    envs = sorted(env_data.keys())
    latencies = []
    error_bars = []
    
    for env in envs:
        slm_vals = [r["slm_per_diag_mean"] for r in env_data[env]]
        latencies.append(mean(slm_vals))
        error_bars.append([r["slm_per_diag_std"] for r in env_data[env]])
    
    colors = {
        "jetson-nano": "#1F1F1F",      # Dark gray
        "jetson-orin": "#737373",      # Medium gray
        "desktop-legion": "#D3D3D3"    # Light gray
    }
    bar_colors = [colors.get(env, "#999") for env in envs]
    
    ax1.bar(envs, latencies, color=bar_colors, alpha=0.7, edgecolor="black", linewidth=1.5)
    ax1.axhline(y=1.0, color="red", linestyle="--", linewidth=2, label="Target (1.0s)")
    ax1.set_ylabel("Latency (s)", fontsize=12, fontweight="bold")
    ax1.set_title("SLM Latency by Environment\n(lower = better)", fontsize=13, fontweight="bold")
    ax1.legend()
    ax1.grid(axis="y", alpha=0.3)
    
    for i, (env, lat) in enumerate(zip(envs, latencies)):
        ax1.text(i, lat + 0.1, f"{lat:.3f}s", ha="center", fontweight="bold")
    
    # Plot 2: Throughput (diag/sec) by environment
    throughputs = []
    for env in envs:
        slm_vals = [r["slm_per_diag_mean"] for r in env_data[env]]
        throughput = 1.0 / mean(slm_vals)  # diag/sec
        throughputs.append(throughput)
    
    ax2.bar(envs, throughputs, color=bar_colors, alpha=0.7, edgecolor="black", linewidth=1.5)
    ax2.axhline(y=1.0, color="green", linestyle="--", linewidth=2, label="Target (1.0 diag/s)")
    ax2.set_ylabel("Throughput (diagnoses/s)", fontsize=12, fontweight="bold")
    ax2.set_title("Throughput by Environment\n(higher = better)", fontsize=13, fontweight="bold")
    ax2.legend()
    ax2.grid(axis="y", alpha=0.3)
    
    for i, (env, tp) in enumerate(zip(envs, throughputs)):
        ax2.text(i, tp + 0.05, f"{tp:.2f}", ha="center", fontweight="bold")
    
    plt.tight_layout()
    output_file = output_dir / "01_env_performance.png"
    plt.savefig(output_file, dpi=300, bbox_inches="tight")
    print(f"✅ Saved: {output_file}")
    plt.close()


if __name__ == "__main__":
    loader = BenchmarkLoader(Path("../../outputs"))
    plot_env_performance(loader, Path("./"))
