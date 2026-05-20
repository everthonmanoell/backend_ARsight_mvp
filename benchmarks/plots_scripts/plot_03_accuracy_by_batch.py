"""
Plot 3: Accuracy by batch and environment.

Shows whether there are performance differences across evaluated batches.

Generated file:
- 03_accuracy_by_batch.png
"""

import sys
from collections import defaultdict
from pathlib import Path
from statistics import mean
from typing import DefaultDict, Dict, List

import matplotlib.pyplot as plt
import numpy as np

# Allow importing local plotting utilities when running from the project root.
SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from data_loader import BenchmarkLoader


ENV_COLORS = {
    "jetson-nano": "#1F1F1F",       # Dark gray.
    "jetson-orin": "#737373",       # Medium gray.
    "desktop-legion": "#D3D3D3",    # Light gray.
}

ENV_LABELS = {
    "jetson-nano": "Jetson Nano",
    "jetson-orin": "Jetson AGX Orin",
    "desktop-legion": "Desktop Legion",
}


def plot_accuracy_by_batch(loader: BenchmarkLoader, output_dir: Path) -> None:
    """Generate an accuracy chart grouped by batch and environment."""
    output_dir.mkdir(parents=True, exist_ok=True)

    # Group records by (batch, environment).
    batch_env_data: DefaultDict[str, DefaultDict[str, List[float]]] = defaultdict(
        lambda: defaultdict(list)
    )

    for record in loader.data:
        batch = record["batch"]
        environment = record["environment"]
        batch_env_data[batch][environment].append(record["accuracy"])

    batches = sorted(batch_env_data.keys())

    envs_all = set()
    for batch_data in batch_env_data.values():
        envs_all.update(batch_data.keys())
    envs = sorted(envs_all)

    x = np.arange(len(batches))
    width = 0.25

    fig, ax = plt.subplots(figsize=(12, 6))

    for idx, env in enumerate(envs):
        accuracies = []

        for batch in batches:
            if env in batch_env_data[batch] and batch_env_data[batch][env]:
                accuracies.append(mean(batch_env_data[batch][env]))
            else:
                accuracies.append(0)

        ax.bar(
            x + idx * width,
            accuracies,
            width,
            label=ENV_LABELS.get(env, env),
            color=ENV_COLORS.get(env, "#999999"),
            alpha=0.7,
            edgecolor="black",
        )

    ax.set_ylabel("Accuracy (%)", fontsize=12, fontweight="bold")
    ax.set_xlabel("Batch", fontsize=12, fontweight="bold")
    ax.set_title("Accuracy by Batch and Environment", fontsize=13, fontweight="bold")
    ax.set_xticks(x + width)
    ax.set_xticklabels(batches)
    ax.set_ylim([95, 101])
    ax.legend(fontsize=10)
    ax.grid(axis="y", alpha=0.3)
    ax.spines[["top", "right"]].set_visible(False)

    plt.tight_layout()

    output_file = output_dir / "03_accuracy_by_batch.png"
    plt.savefig(output_file, dpi=300, bbox_inches="tight")
    plt.close(fig)

    print(f"Saved: {output_file}")


if __name__ == "__main__":
    project_root = SCRIPT_DIR.parent.parent
    loader = BenchmarkLoader(project_root / "outputs")
    plot_accuracy_by_batch(loader, SCRIPT_DIR.parent / "plots_output")