"""
Plot 2: Model Comparison - SEPARATED INTO TWO PLOT FILES
- SLM Latency by Model (02_model_latency.png)
- Accuracy by Model (02_model_accuracy.png)
"""

import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
from data_loader import BenchmarkLoader
from statistics import mean


def plot_model_latency(loader: BenchmarkLoader, output_dir: Path) -> None:
    """Creates chart comparing model latency"""
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    summary = loader.summary_by_env_model()
    
    # Agrupa por model
    model_data = {}
    for row in summary:
        model = row["model"].lower()
        # Exclude CPU-only variants for main comparison
        if model.endswith("-cpu"):
            continue
        if model not in model_data:
            model_data[model] = {}
        model_data[model][row["environment"]] = row
    
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
    
    fig, ax = plt.subplots(figsize=(12, 6))
    
    for i, env in enumerate(envs):
        latencies = []
        for model in models:
            if model in model_data and env in model_data[model]:
                latencies.append(model_data[model][env]["slm_per_diag_mean"])
            else:
                latencies.append(0)
        
        ax.bar(x + i*width, latencies, width, label=env, color=colors.get(env, "#999"), alpha=0.7, edgecolor="black")
    
    ax.axhline(y=1.0, color="red", linestyle="--", linewidth=2, label="Target (1.0s)")
    ax.set_ylabel("SLM Latency (s)", fontsize=12, fontweight="bold")
    ax.set_title("SLM Latency by Model (All Environments)\n(lower = better)", fontsize=13, fontweight="bold")
    ax.set_xticks(x + width)
    ax.set_xticklabels(models, fontsize=11)
    ax.legend(fontsize=10)
    ax.grid(axis="y", alpha=0.3)
    
    plt.tight_layout()
    output_file = output_dir / "02_model_latency.png"
    plt.savefig(output_file, dpi=300, bbox_inches="tight")
    print(f"✅ Saved: {output_file}")
    plt.close()


def plot_model_accuracy(loader: BenchmarkLoader, output_dir: Path) -> None:
    """Creates chart comparing model accuracy"""
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    summary = loader.summary_by_env_model()
    
    # Agrupa por model
    model_data = {}
    for row in summary:
        model = row["model"].lower()
        # Exclude CPU-only variants for main comparison
        if model.endswith("-cpu"):
            continue
        if model not in model_data:
            model_data[model] = {}
        model_data[model][row["environment"]] = row
    
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
    
    fig, ax = plt.subplots(figsize=(12, 6))
    
    for i, env in enumerate(envs):
        accs = []
        for model in models:
            if model in model_data and env in model_data[model]:
                accs.append(model_data[model][env]["accuracy_mean"])
            else:
                accs.append(0)
        
        ax.bar(x + i*width, accs, width, label=env, color=colors.get(env, "#999"), alpha=0.7, edgecolor="black")
    
    ax.set_ylabel("Accuracy (%)", fontsize=12, fontweight="bold")
    ax.set_title("Accuracy by Model (All Environments)\n(higher = better)", fontsize=13, fontweight="bold")
    ax.set_xticks(x + width)
    ax.set_xticklabels(models, fontsize=11)
    ax.set_ylim([90, 105])
    ax.legend(fontsize=10)
    ax.grid(axis="y", alpha=0.3)
    
    plt.tight_layout()
    output_file = output_dir / "02_model_accuracy.png"
    plt.savefig(output_file, dpi=300, bbox_inches="tight")
    print(f"✅ Saved: {output_file}")
    plt.close()


def plot_model_comparison(loader: BenchmarkLoader, output_dir: Path) -> None:
    """Wrapper function that calls both separated plots"""
    plot_model_latency(loader, output_dir)
    plot_model_accuracy(loader, output_dir)


if __name__ == "__main__":
    loader = BenchmarkLoader(Path("../../outputs"))
    plot_model_comparison(loader, Path("./"))
    ax2.grid(axis="y", alpha=0.3)
    
    plt.tight_layout()
    output_file = output_dir / "02_model_comparison.png"
    plt.savefig(output_file, dpi=300, bbox_inches="tight")
    print(f"✅ Saved: {output_file}")
    plt.close()


if __name__ == "__main__":
    loader = BenchmarkLoader(Path("../../outputs"))
    plot_model_comparison(loader, Path("./"))
