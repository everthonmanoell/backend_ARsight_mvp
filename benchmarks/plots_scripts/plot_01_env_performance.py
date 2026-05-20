"""
Plot 1: SLM latency and throughput by platform.

Generated files:
- 01_env_latency.png
- 01_env_throughput.png
"""

import sys
from pathlib import Path
from statistics import mean
from typing import Dict, List

import matplotlib.pyplot as plt

# Allow importing local plotting utilities when running from the project root.
SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from data_loader import BenchmarkLoader


PLATFORM_COLORS = {
    "desktop-legion": "#2196F3",
    "jetson-nano": "#FF9800",
    "jetson-orin": "#4CAF50",
}

PLATFORM_LABELS = {
    "desktop-legion": "Desktop Legion",
    "jetson-nano": "Jetson Nano",
    "jetson-orin": "Jetson AGX Orin",
}


def _aggregate_by_env(loader: BenchmarkLoader) -> Dict[str, List[float]]:
    """Return mean SLM latencies grouped by execution environment."""
    env_data: Dict[str, List[float]] = {}

    for row in loader.summary_by_env_model():
        env_data.setdefault(row["environment"], []).append(row["slm_per_diag_mean"])

    return env_data


def plot_env_latency(loader: BenchmarkLoader, output_dir: Path) -> None:
    """Generate the SLM latency plot grouped by execution environment."""
    output_dir.mkdir(parents=True, exist_ok=True)

    env_data = _aggregate_by_env(loader)
    envs = sorted(env_data.keys())

    latencies = [mean(env_data[env]) for env in envs]
    labels = [PLATFORM_LABELS.get(env, env) for env in envs]
    colors = [PLATFORM_COLORS.get(env, "#999999") for env in envs]

    fig, ax = plt.subplots(figsize=(8, 5))

    bars = ax.bar(
        labels,
        latencies,
        color=colors,
        alpha=0.85,
        edgecolor="white",
        linewidth=1.2,
        width=0.5,
    )

    ax.axhline(
        1.0,
        color="#E53935",
        linestyle="--",
        linewidth=1.6,
        label="Target (1.0s)",
    )

    # Value labels.
    for bar, latency in zip(bars, latencies):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 0.08,
            f"{latency:.3f}s",
            ha="center",
            va="bottom",
            fontsize=11,
            fontweight="bold",
        )

    ax.set_ylabel("Latency (s)", fontsize=12, fontweight="bold")
    ax.set_title(
        "SLM Latency by Environment\n(lower = better)",
        fontsize=13,
        fontweight="bold",
    )
    ax.set_ylim(bottom=0)
    ax.legend(fontsize=11)
    ax.grid(axis="y", alpha=0.25)
    ax.spines[["top", "right"]].set_visible(False)

    plt.tight_layout()

    output_path = output_dir / "01_env_latency.png"
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close(fig)

    print(f"Saved: {output_path}")


def plot_env_throughput(loader: BenchmarkLoader, output_dir: Path) -> None:
    """Generate the throughput plot grouped by execution environment."""
    output_dir.mkdir(parents=True, exist_ok=True)

    env_data = _aggregate_by_env(loader)
    envs = sorted(env_data.keys())

    throughputs = [1.0 / mean(env_data[env]) for env in envs]
    labels = [PLATFORM_LABELS.get(env, env) for env in envs]
    colors = [PLATFORM_COLORS.get(env, "#999999") for env in envs]

    fig, ax = plt.subplots(figsize=(8, 5))

    bars = ax.bar(
        labels,
        throughputs,
        color=colors,
        alpha=0.85,
        edgecolor="white",
        linewidth=1.2,
        width=0.5,
    )

    ax.axhline(
        1.0,
        color="#E53935",
        linestyle="--",
        linewidth=1.6,
        label="Target (1.0 diag/s)",
    )

    # Value labels.
    for bar, throughput in zip(bars, throughputs):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 0.04,
            f"{throughput:.2f}",
            ha="center",
            va="bottom",
            fontsize=11,
            fontweight="bold",
        )

    ax.set_ylabel("Throughput (diagnoses/s)", fontsize=12, fontweight="bold")
    ax.set_title(
        "Throughput by Environment\n(higher = better)",
        fontsize=13,
        fontweight="bold",
    )
    ax.set_ylim(bottom=0)
    ax.legend(fontsize=11)
    ax.grid(axis="y", alpha=0.25)
    ax.spines[["top", "right"]].set_visible(False)

    plt.tight_layout()

    output_path = output_dir / "01_env_throughput.png"
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close(fig)

    print(f"Saved: {output_path}")


def plot_env_performance(loader: BenchmarkLoader, output_dir: Path) -> None:
    """Generate latency and throughput plots grouped by execution environment."""
    plot_env_latency(loader, output_dir)
    plot_env_throughput(loader, output_dir)


if __name__ == "__main__":
    project_root = SCRIPT_DIR.parent.parent
    loader = BenchmarkLoader(project_root / "outputs")
    plot_env_performance(loader, SCRIPT_DIR.parent / "plots_output")