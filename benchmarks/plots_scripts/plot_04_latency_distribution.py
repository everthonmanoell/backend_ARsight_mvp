"""
Plot 4: Latency Distribution (Boxplot)
Shows latency variability and outliers
"""

import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
from data_loader import BenchmarkLoader


def plot_latency_distribution(loader: BenchmarkLoader, output_dir: Path) -> None:
    """Creates latency distribution boxplot"""
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Agrupa por environment
    env_latencies = {}
    
    for record in loader.data:
        env = record["environment"]
        if env not in env_latencies:
            env_latencies[env] = []
        env_latencies[env].append(record["slm_per_diagnosis_s"])
    
    envs = sorted(env_latencies.keys())
    data_to_plot = [env_latencies[env] for env in envs]
    
    # Academic palette: high-contrast grays
    colors = {
        "jetson-nano": "#1F1F1F",      # Dark gray
        "jetson-orin": "#737373",      # Medium gray
        "desktop-legion": "#D3D3D3"    # Light gray
    }
    
    fig, ax = plt.subplots(figsize=(11, 6.5))
    
    bp = ax.boxplot(data_to_plot, labels=[e.replace("-", "\n") for e in envs], 
                    patch_artist=True, notch=True, showmeans=True,
                    meanprops=dict(marker="D", markerfacecolor="red", markersize=6))
    
    # Colorir boxes
    for patch, env in zip(bp["boxes"], envs):
        patch.set_facecolor(colors.get(env, "#3D3D3D"))
        patch.set_alpha(0.75)
        patch.set_linewidth(1.5)
    
    # Estilo dos whiskers e medians
    for whisker in bp["whiskers"]:
        whisker.set(linewidth=1.5, color="#333")
    for median in bp["medians"]:
        median.set(linewidth=2, color="#000")
    
    ax.axhline(y=1.0, color="#C41E3A", linestyle="--", linewidth=2.5, label="Target (1.0s)", alpha=0.8)
    ax.set_ylabel("SLM Latency (s)", fontsize=12, fontweight="bold")
    ax.set_title("SLM Latency Distribution by Environment\n(Boxplot: median, quartiles, min/max)", 
                fontsize=13, fontweight="bold", pad=15)
    ax.legend(fontsize=11, loc="upper right")
    ax.grid(axis="y", alpha=0.25, linestyle=":", linewidth=0.8)
    ax.set_ylim(bottom=0)
    
    # Add statistics table below chart
    stats_text = "\nStatistics by Environment:"
    for i, env in enumerate(envs):
        vals = env_latencies[env]
        min_val = np.min(vals)
        max_val = np.max(vals)
        median_val = np.median(vals)
        mean_val = np.mean(vals)
        std_val = np.std(vals)
        
        stats_text += f"\n  {env}: μ={mean_val:.3f}s ± {std_val:.3f}s | med={median_val:.3f}s | [{min_val:.3f}...{max_val:.3f}]s"
    
    # Add stats text as footer annotation
    fig.text(0.5, -0.05, stats_text, ha="center", fontsize=9, family="monospace",
            bbox=dict(boxstyle="round,pad=0.8", facecolor="#F5F5F5", edgecolor="#999", alpha=0.8))
    
    plt.tight_layout()
    plt.subplots_adjust(bottom=0.25)  # Espaço para a tabela de stats
    output_file = output_dir / "04_latency_distribution.png"
    plt.savefig(output_file, dpi=300, bbox_inches="tight")
    print(f"✅ Saved: {output_file}")
    plt.close()


if __name__ == "__main__":
    loader = BenchmarkLoader(Path("../../outputs"))
    plot_latency_distribution(loader, Path("./"))
