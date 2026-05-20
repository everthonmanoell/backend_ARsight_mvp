"""
Plot 9: Desktop Legion performance by model.

Generates separated plots for latency, throughput, and target success rate.
Includes the Qwen CPU variant only when it is the only available option.

Generated files:
- 09_desktop_legion_latency.png
- 09_desktop_legion_throughput.png
- 09_desktop_legion_success.png
"""

import sys
from pathlib import Path
from typing import Dict, List

import matplotlib.pyplot as plt
import numpy as np

# Allow importing local plotting utilities when running from the project root.
SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from data_loader import BenchmarkLoader


PALETTE = {
    "dialogpt": {"face": "#D7F8D7", "edge": "#000000", "label": "DialoGPT"},
    "phi": {"face": "#9FE1CB", "edge": "#000000", "label": "Phi"},
    "qwen": {"face": "#518A58", "edge": "#000000", "label": "Qwen GPU"},
    "qwen-gpu": {"face": "#0C4D0C", "edge": "#000000", "label": "Qwen GPU"},
    "qwen-cpu": {"face": "#3CFD35", "edge": "#000000", "label": "Qwen CPU"},
}


def _get_legion_summary(loader: BenchmarkLoader) -> Dict[str, dict]:
    """Return Desktop Legion summary data indexed by model name."""
    legion_data = {}

    for row in loader.summary_by_env_model():
        if row["environment"] == "desktop-legion":
            model = row["model"].lower()
            legion_data[model] = row

    return legion_data


def _get_display_models(model_data: Dict[str, dict]) -> List[str]:
    """
    Return models to display.

    CPU-only variants are excluded from the main comparison unless they are the
    only available option.
    """
    display_models = [
        model
        for model in sorted(model_data.keys())
        if not model.endswith("-cpu") or len(model_data) == 1
    ]

    if not display_models:
        display_models = sorted(model_data.keys())

    return display_models


def _model_labels(models: List[str]) -> List[str]:
    """Return display labels for model names."""
    return [PALETTE.get(model, {}).get("label", model) for model in models]


def _face_colors(models: List[str]) -> List[str]:
    """Return face colors for model names."""
    return [PALETTE.get(model, {}).get("face", "#999999") for model in models]


def _edge_colors(models: List[str]) -> List[str]:
    """Return edge colors for model names."""
    return [PALETTE.get(model, {}).get("edge", "#333333") for model in models]


def plot_desktop_legion_latency(loader: BenchmarkLoader, output_dir: Path) -> None:
    """Generate a Desktop Legion latency chart grouped by model."""
    output_dir.mkdir(parents=True, exist_ok=True)

    legion_data = _get_legion_summary(loader)

    if not legion_data:
        print("No Desktop Legion data found.")
        return

    display_models = _get_display_models(legion_data)
    model_labels = _model_labels(display_models)
    face_colors = _face_colors(display_models)
    edge_colors = _edge_colors(display_models)

    x = np.arange(len(display_models))
    latencies = [legion_data[model]["slm_per_diag_mean"] for model in display_models]
    errors = [legion_data[model]["slm_per_diag_std"] for model in display_models]

    fig, ax = plt.subplots(figsize=(10, 6))

    bars = ax.bar(
        x,
        latencies,
        color=face_colors,
        edgecolor=edge_colors,
        linewidth=1.5,
        width=0.6,
        alpha=0.8,
    )

    for idx, (latency, error, edge_color) in enumerate(
        zip(latencies, errors, edge_colors)
    ):
        ax.errorbar(
            idx,
            latency,
            yerr=error,
            fmt="none",
            ecolor=edge_color,
            elinewidth=1.5,
            capsize=5,
            capthick=1.5,
            zorder=3,
        )

    ax.axhline(
        y=1.0,
        color="#E24B4A",
        linestyle="--",
        linewidth=2,
        label="Target (1.0s)",
        zorder=4,
    )

    ax.set_xticks(x)
    ax.set_xticklabels(model_labels, fontsize=11)
    ax.set_ylim(0, max(latencies) * 1.3)
    ax.set_ylabel("Latency (s)", fontsize=12, fontweight="bold")
    ax.set_title(
        "Desktop Legion: SLM Latency by Model\n(lower = better)",
        fontsize=13,
        fontweight="bold",
        pad=15,
    )
    ax.grid(axis="y", alpha=0.3)
    ax.legend(fontsize=11, frameon=False)
    ax.spines[["top", "right"]].set_visible(False)

    for bar, value, error in zip(bars, latencies, errors):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            value + error + 0.1,
            f"{value:.3f}s",
            ha="center",
            va="bottom",
            fontsize=11,
            fontweight="bold",
        )

    plt.tight_layout()

    output_file = output_dir / "09_desktop_legion_latency.png"
    plt.savefig(output_file, dpi=300, bbox_inches="tight")
    plt.close(fig)

    print(f"Saved: {output_file}")


def plot_desktop_legion_throughput(loader: BenchmarkLoader, output_dir: Path) -> None:
    """Generate a Desktop Legion throughput chart grouped by model."""
    output_dir.mkdir(parents=True, exist_ok=True)

    legion_data = _get_legion_summary(loader)

    if not legion_data:
        print("No Desktop Legion data found.")
        return

    display_models = _get_display_models(legion_data)
    model_labels = _model_labels(display_models)
    face_colors = _face_colors(display_models)
    edge_colors = _edge_colors(display_models)

    x = np.arange(len(display_models))
    throughputs = [
        1.0 / legion_data[model]["slm_per_diag_mean"]
        for model in display_models
    ]

    fig, ax = plt.subplots(figsize=(10, 6))

    bars = ax.bar(
        x,
        throughputs,
        color=face_colors,
        edgecolor=edge_colors,
        linewidth=1.5,
        width=0.6,
        alpha=0.8,
    )

    ax.axhline(
        y=1.0,
        color="#22C55E",
        linestyle="--",
        linewidth=2,
        label="Target (1.0 diag/s)",
        zorder=4,
    )

    ax.set_xticks(x)
    ax.set_xticklabels(model_labels, fontsize=11)
    ax.set_ylim(0, max(throughputs) * 1.3)
    ax.set_ylabel("Throughput (diagnoses/s)", fontsize=12, fontweight="bold")
    ax.set_title(
        "Desktop Legion: Throughput by Model\n(higher = better)",
        fontsize=13,
        fontweight="bold",
        pad=15,
    )
    ax.grid(axis="y", alpha=0.3)
    ax.legend(fontsize=11, frameon=False)
    ax.spines[["top", "right"]].set_visible(False)

    for bar, value in zip(bars, throughputs):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            value + 0.05,
            f"{value:.2f}",
            ha="center",
            va="bottom",
            fontsize=11,
            fontweight="bold",
        )

    plt.tight_layout()

    output_file = output_dir / "09_desktop_legion_throughput.png"
    plt.savefig(output_file, dpi=300, bbox_inches="tight")
    plt.close(fig)

    print(f"Saved: {output_file}")


def plot_desktop_legion_success(loader: BenchmarkLoader, output_dir: Path) -> None:
    """Generate a Desktop Legion target success-rate chart grouped by model."""
    output_dir.mkdir(parents=True, exist_ok=True)

    target_rates = {}

    for record in loader.data:
        if record["environment"] == "desktop-legion":
            model = record["model"].lower()

            if model not in target_rates:
                target_rates[model] = {"success": 0, "total": 0}

            target_rates[model]["total"] += 1

            if record["slm_per_diagnosis_s"] <= 1.0:
                target_rates[model]["success"] += 1

    if not target_rates:
        print("No Desktop Legion data found.")
        return

    display_models = _get_display_models(target_rates)
    model_labels = _model_labels(display_models)
    face_colors = _face_colors(display_models)
    edge_colors = _edge_colors(display_models)

    x = np.arange(len(display_models))
    success_rates = []

    for model in display_models:
        success = target_rates[model]["success"]
        total = max(1, target_rates[model]["total"])
        success_rates.append(success / total * 100)

    fig, ax = plt.subplots(figsize=(10, 6))

    bars = ax.bar(
        x,
        success_rates,
        color=face_colors,
        edgecolor=edge_colors,
        linewidth=1.5,
        width=0.6,
        alpha=0.8,
    )

    ax.axhline(
        y=100.0,
        color="#22C55E",
        linestyle="--",
        linewidth=2,
        label="Target (100%)",
        zorder=4,
    )

    ax.set_xticks(x)
    ax.set_xticklabels(model_labels, fontsize=11)
    ax.set_ylim(0, 110)
    ax.set_ylabel("Target Success Rate (%)", fontsize=12, fontweight="bold")
    ax.set_title(
        "Desktop Legion: Target Met Rate by Model\n(higher = better)",
        fontsize=13,
        fontweight="bold",
        pad=15,
    )
    ax.grid(axis="y", alpha=0.3)
    ax.legend(fontsize=11, frameon=False)
    ax.spines[["top", "right"]].set_visible(False)

    for bar, rate, model in zip(bars, success_rates, display_models):
        success = target_rates[model]["success"]
        total = target_rates[model]["total"]

        ax.text(
            bar.get_x() + bar.get_width() / 2,
            rate + 2,
            f"{rate:.1f}%\n({success}/{total})",
            ha="center",
            va="bottom",
            fontsize=10,
            fontweight="bold",
        )

    plt.tight_layout()

    output_file = output_dir / "09_desktop_legion_success.png"
    plt.savefig(output_file, dpi=300, bbox_inches="tight")
    plt.close(fig)

    print(f"Saved: {output_file}")


def plot_desktop_legion(loader: BenchmarkLoader, output_dir: Path) -> None:
    """Generate all Desktop Legion performance plots."""
    plot_desktop_legion_latency(loader, output_dir)
    plot_desktop_legion_throughput(loader, output_dir)
    plot_desktop_legion_success(loader, output_dir)


if __name__ == "__main__":
    project_root = SCRIPT_DIR.parent.parent
    loader = BenchmarkLoader(project_root / "outputs")
    plot_desktop_legion(loader, SCRIPT_DIR.parent / "plots_output")