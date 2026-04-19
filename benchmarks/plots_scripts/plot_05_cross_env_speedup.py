"""
Plot 5: Cross-Environment Comparison (Speedup vs Desktop Legion)
Shows how much faster/slower vs baseline
"""

import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
from data_loader import BenchmarkLoader
from statistics import mean


def plot_cross_env_comparison(loader: BenchmarkLoader, output_dir: Path) -> None:
    """Creates speedup chart vs Desktop Legion"""
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    summary = loader.summary_by_env_model()
    
    # Agrupa por model, depois por environment
    model_env_data = {}
    for row in summary:
        model = row["model"].lower()
        if model not in model_env_data:
            model_env_data[model] = {}
        model_env_data[model][row["environment"]] = row["slm_per_diag_mean"]
    
    # Calcula speedup vs desktop-legion
    speedups = {}
    for model, env_data in model_env_data.items():
        if "desktop-legion" not in env_data:
            continue
        
        baseline = env_data["desktop-legion"]
        speedups[model] = {}
        
        for env, latency in env_data.items():
            speedup = baseline / latency
            speedups[model][env] = speedup
    
    fig, ax = plt.subplots(figsize=(10, 6))
    
    models = sorted(speedups.keys())
    envs_all = set()
    for env_data in speedups.values():
        envs_all.update(env_data.keys())
    envs = sorted(envs_all)
    
    x = np.arange(len(models))
    width = 0.25
    
    colors = {
        "jetson-nano": "#1F1F1F",      # Dark gray
        "jetson-orin": "#737373",      # Medium gray
        "desktop-legion": "#D3D3D3"    # Light gray
    }
    
    for i, env in enumerate(envs):
        speedup_vals = []
        for model in models:
            if env in speedups[model]:
                speedup_vals.append(speedups[model][env])
            else:
                speedup_vals.append(0)
        
        ax.bar(x + i*width, speedup_vals, width, label=env, color=colors.get(env, "#999"), alpha=0.7)
    
    ax.axhline(y=1.0, color="black", linestyle="-", linewidth=1.5, label="Baseline (1.0x)")
    ax.set_ylabel("Speedup (lower latency = speedup > 1)", fontsize=12, fontweight="bold")
    ax.set_xlabel("Model", fontsize=12, fontweight="bold")
    ax.set_title("Speedup vs Desktop Legion Baseline\n(>1.0 = faster, <1.0 = slower)", fontsize=13, fontweight="bold")
    ax.set_xticks(x + width)
    ax.set_xticklabels(models)
    ax.legend()
    ax.grid(axis="y", alpha=0.3)
    
    plt.tight_layout()
    output_file = output_dir / "05_cross_env_speedup.png"
    plt.savefig(output_file, dpi=300, bbox_inches="tight")
    print(f"✅ Saved: {output_file}")
    plt.close()


if __name__ == "__main__":
    loader = BenchmarkLoader(Path("../../outputs"))
    plot_cross_env_comparison(loader, Path("./"))
