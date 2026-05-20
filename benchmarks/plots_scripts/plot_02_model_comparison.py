"""
Plot 2: Model comparison.

Generated files:
- 02_model_latency.png
- 02_model_accuracy.png
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


def _collect_model_data(loader: BenchmarkLoader) -> Dict[str, Dict[str, dict]]:
    """
    Collect benchmark summaries grouped by model and environment.

    CPU-only model variants are excluded from the main comparison to keep the
    chart focused on standard GPU-oriented runs.
    """
    summary = loader.summary_by_env_model()
    model_data: Dict[str, Dict[str, dict]] = {}

    for row in summary:
        model = row["model"].lower()

        # Exclude CPU-only variants from the main comparison.
        if model.endswith("-cpu"):
            continue

        if model not in model_data:
            model_data[model] = {}

        model_data[model][row["environment"]] = row

    return model_data


def _get_models_and_envs(model_data: Dict[str, Dict[str, dict]]):
    """Return sorted model and environment labels present in the benchmark data."""
    models = sorted(model_data.keys())

    envs_in_data = set()
    for model_envs in model_data.values():
        envs_in_data.update(model_envs.keys())

    envs = sorted(envs_in_data)

    return models, envs


def plot_model_latency(loader: BenchmarkLoader, output_dir: Path) -> None:
    """Generate a grouped bar chart comparing SLM latency by model."""
    output_dir.mkdir(parents=True, exist_ok=True)

    model_data = _collect_model_data(loader)
    models, envs = _get_models_and_envs(model_data)

    x = np.arange(len(models))
    width = 0.25

    fig, ax = plt.subplots(figsize=(12, 6))

    for idx, env in enumerate(envs):
        latencies = []

        for model in models:
            if env in model_data.get(model, {}):
                latencies.append(model_data[model][env]["slm_per_diag_mean"])
            else:
                latencies.append(0)

        ax.bar(
            x + idx * width,
            latencies,
            width,
            label=ENV_LABELS.get(env, env),
            color=ENV_COLORS.get(env, "#999999"),
            alpha=0.7,
            edgecolor="black",
        )

    ax.axhline(
        y=1.0,
        color="red",
        linestyle="--",
        linewidth=2,
        label="Target (1.0s)",
    )

    ax.set_ylabel("SLM Latency (s)", fontsize=12, fontweight="bold")
    ax.set_title(
        "SLM Latency by Model (All Environments)\n(lower = better)",
        fontsize=13,
        fontweight="bold",
    )

    ax.set_xticks(x + width)
    ax.set_xticklabels(models, fontsize=11)
    ax.legend(fontsize=10)
    ax.grid(axis="y", alpha=0.3)
    ax.spines[["top", "right"]].set_visible(False)

    plt.tight_layout()

    output_file = output_dir / "02_model_latency.png"
    plt.savefig(output_file, dpi=300, bbox_inches="tight")
    plt.close(fig)

    print(f"Saved: {output_file}")


def plot_model_accuracy(loader: BenchmarkLoader, output_dir: Path) -> None:
    """Generate a grouped bar chart comparing accuracy by model."""
    output_dir.mkdir(parents=True, exist_ok=True)

    model_data = _collect_model_data(loader)
    models, envs = _get_models_and_envs(model_data)

    x = np.arange(len(models))
    width = 0.25

    fig, ax = plt.subplots(figsize=(12, 6))

    for idx, env in enumerate(envs):
        accuracies = []

        for model in models:
            if env in model_data.get(model, {}):
                accuracies.append(model_data[model][env]["accuracy_mean"])
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
    ax.set_title(
        "Accuracy by Model (All Environments)\n(higher = better)",
        fontsize=13,
        fontweight="bold",
    )

    ax.set_xticks(x + width)
    ax.set_xticklabels(models, fontsize=11)
    ax.set_ylim([90, 105])
    ax.legend(fontsize=10)
    ax.grid(axis="y", alpha=0.3)
    ax.spines[["top", "right"]].set_visible(False)

    plt.tight_layout()

    output_file = output_dir / "02_model_accuracy.png"
    plt.savefig(output_file, dpi=300, bbox_inches="tight")
    plt.close(fig)

    print(f"Saved: {output_file}")


def plot_model_comparison(loader: BenchmarkLoader, output_dir: Path) -> None:
    """Generate the separated model comparison plots."""
    plot_model_latency(loader, output_dir)
    plot_model_accuracy(loader, output_dir)


if __name__ == "__main__":
    project_root = SCRIPT_DIR.parent.parent
    loader = BenchmarkLoader(project_root / "outputs")
    plot_model_comparison(loader, SCRIPT_DIR.parent / "plots_output")