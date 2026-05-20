"""
Plot 5: Cross-environment comparison.

Shows relative speedup versus the Desktop Legion baseline.

Generated file:
- 05_cross_env_speedup.png
"""

import sys
from pathlib import Path
from typing import Dict

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


def plot_cross_env_comparison(loader: BenchmarkLoader, output_dir: Path) -> None:
    """Generate a speedup chart relative to the Desktop Legion baseline."""
    output_dir.mkdir(parents=True, exist_ok=True)

    summary = loader.summary_by_env_model()

    # Group by model, then by environment.
    model_env_data: Dict[str, Dict[str, float]] = {}

    for row in summary:
        model = row["model"].lower()

        if model not in model_env_data:
            model_env_data[model] = {}

        model_env_data[model][row["environment"]] = row["slm_per_diag_mean"]

    # Compute speedup relative to Desktop Legion.
    speedups: Dict[str, Dict[str, float]] = {}

    for model, env_data in model_env_data.items():
        if "desktop-legion" not in env_data:
            continue

        baseline = env_data["desktop-legion"]
        speedups[model] = {}

        for env, latency in env_data.items():
            speedup = baseline / latency
            speedups[model][env] = speedup

    models = sorted(speedups.keys())

    envs_all = set()
    for env_data in speedups.values():
        envs_all.update(env_data.keys())
    envs = sorted(envs_all)

    x = np.arange(len(models))
    width = 0.25

    fig, ax = plt.subplots(figsize=(10, 6))

    for idx, env in enumerate(envs):
        speedup_values = []

        for model in models:
            if env in speedups[model]:
                speedup_values.append(speedups[model][env])
            else:
                speedup_values.append(0)

        ax.bar(
            x + idx * width,
            speedup_values,
            width,
            label=ENV_LABELS.get(env, env),
            color=ENV_COLORS.get(env, "#999999"),
            alpha=0.7,
            edgecolor="black",
        )

    ax.axhline(
        y=1.0,
        color="black",
        linestyle="-",
        linewidth=1.5,
        label="Baseline (1.0x)",
    )

    ax.set_ylabel(
        "Speedup (speedup > 1 means lower latency)",
        fontsize=12,
        fontweight="bold",
    )
    ax.set_xlabel("Model", fontsize=12, fontweight="bold")
    ax.set_title(
        "Speedup Relative to Desktop Legion\n"
        "(>1.0 = faster, <1.0 = slower)",
        fontsize=13,
        fontweight="bold",
    )
    ax.set_xticks(x + width)
    ax.set_xticklabels(models)
    ax.legend(fontsize=10)
    ax.grid(axis="y", alpha=0.3)
    ax.spines[["top", "right"]].set_visible(False)

    plt.tight_layout()

    output_file = output_dir / "05_cross_env_speedup.png"
    plt.savefig(output_file, dpi=300, bbox_inches="tight")
    plt.close(fig)

    print(f"Saved: {output_file}")


if __name__ == "__main__":
    project_root = SCRIPT_DIR.parent.parent
    loader = BenchmarkLoader(project_root / "outputs")
    plot_cross_env_comparison(loader, SCRIPT_DIR.parent / "plots_output")