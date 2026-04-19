"""
Plot 3: Accuracy by Batch and Environment
Shows if there are performance differences between batches
"""

import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
from data_loader import BenchmarkLoader
from statistics import mean
from collections import defaultdict


def plot_accuracy_by_batch(loader: BenchmarkLoader, output_dir: Path) -> None:
    """Creates accuracy chart by batch"""
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Agrupa por (batch, environment)
    batch_env_data = defaultdict(lambda: defaultdict(list))
    
    for record in loader.data:
        batch = record["batch"]
        env = record["environment"]
        batch_env_data[batch][env].append(record["accuracy"])
    
    batches = sorted(batch_env_data.keys())
    envs_all = set()
    for batch_data in batch_env_data.values():
        envs_all.update(batch_data.keys())
    envs = sorted(envs_all)
    
    colors = {
        "jetson-nano": "#1F1F1F",      # Dark gray
        "jetson-orin": "#737373",      # Medium gray
        "desktop-legion": "#D3D3D3"    # Light gray
    }
    x = np.arange(len(batches))
    width = 0.25
    
    fig, ax = plt.subplots(figsize=(12, 6))
    
    for i, env in enumerate(envs):
        accs = []
        for batch in batches:
            if env in batch_env_data[batch] and batch_env_data[batch][env]:
                accs.append(mean(batch_env_data[batch][env]))
            else:
                accs.append(0)
        
        ax.bar(x + i*width, accs, width, label=env, color=colors.get(env, "#999"), alpha=0.7)
    
    ax.set_ylabel("Accuracy (%)", fontsize=12, fontweight="bold")
    ax.set_xlabel("Batch", fontsize=12, fontweight="bold")
    ax.set_title("Accuracy by Batch and Environment", fontsize=13, fontweight="bold")
    ax.set_xticks(x + width)
    ax.set_xticklabels(batches)
    ax.set_ylim([95, 101])
    ax.legend()
    ax.grid(axis="y", alpha=0.3)
    
    plt.tight_layout()
    output_file = output_dir / "03_accuracy_by_batch.png"
    plt.savefig(output_file, dpi=300, bbox_inches="tight")
    print(f"✅ Saved: {output_file}")
    plt.close()


if __name__ == "__main__":
    loader = BenchmarkLoader(Path("../../outputs"))
    plot_accuracy_by_batch(loader, Path("./"))
