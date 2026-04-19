"""
Plot 2: Model Comparison (DialoGPT, Qwen, Phi)
Shows which model is best in each environment
"""

import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
from data_loader import BenchmarkLoader
from statistics import mean


def plot_model_comparison(loader: BenchmarkLoader, output_dir: Path) -> None:
    """Creates chart comparing models"""
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    summary = loader.summary_by_env_model()
    
    # Agrupa por model
    model_data = {}
    for row in summary:
        model = row["model"].lower()
        if model not in model_data:
            model_data[model] = {}
        model_data[model][row["environment"]] = row
    
    # Figura com 2 subplots
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
    
    # Preparar dados
    models = sorted(model_data.keys())
    envs_in_data = set()
    for model_envs in model_data.values():
        envs_in_data.update(model_envs.keys())
    envs = sorted(envs_in_data)
    
    colors = {
        "jetson-nano": "#1F1F1F",      # Dark gray
        "jetson-orin": "#737373",      # Medium gray
        "desktop-legion": "#D3D3D3"    # Light gray
    }
    x = np.arange(len(models))
    width = 0.25
    
    # Plot 1: SLM Latency
    for i, env in enumerate(envs):
        latencies = []
        for model in models:
            if model in model_data and env in model_data[model]:
                latencies.append(model_data[model][env]["slm_per_diag_mean"])
            else:
                latencies.append(0)  # Model not available in this env
        
        ax1.bar(x + i*width, latencies, width, label=env, color=colors.get(env, "#999"), alpha=0.7)
    
    ax1.set_ylabel("SLM Latency (s)", fontsize=12, fontweight="bold")
    ax1.set_title("SLM Latency by Model\n(lower = better)", fontsize=13, fontweight="bold")
    ax1.set_xticks(x + width)
    ax1.set_xticklabels(models)
    ax1.legend()
    ax1.grid(axis="y", alpha=0.3)
    
    # Plot 2: Accuracy
    for i, env in enumerate(envs):
        accs = []
        for model in models:
            if model in model_data and env in model_data[model]:
                accs.append(model_data[model][env]["accuracy_mean"])
            else:
                accs.append(0)
        
        ax2.bar(x + i*width, accs, width, label=env, color=colors.get(env, "#999"), alpha=0.7)
    
    ax2.set_ylabel("Accuracy (%)", fontsize=12, fontweight="bold")
    ax2.set_title("Accuracy by Model\n(higher = better)", fontsize=13, fontweight="bold")
    ax2.set_xticks(x + width)
    ax2.set_xticklabels(models)
    ax2.set_ylim([90, 105])
    ax2.legend()
    ax2.grid(axis="y", alpha=0.3)
    
    plt.tight_layout()
    output_file = output_dir / "02_model_comparison.png"
    plt.savefig(output_file, dpi=300, bbox_inches="tight")
    print(f"✅ Saved: {output_file}")
    plt.close()


if __name__ == "__main__":
    loader = BenchmarkLoader(Path("../../outputs"))
    plot_model_comparison(loader, Path("./"))
