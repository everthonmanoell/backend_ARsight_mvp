"""
Plot 4: Latency distribution by environment.

Shows latency variability, quartiles, and outliers.

Generated file:
- 04_latency_distribution.png
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


ENV_COLORS = {
    "jetson-nano": "#1F1F1F",       # Dark gray.
    "jetson-orin": "#737373",       # Medium gray.
    "desktop-legion": "#D3D3D3",    # Light gray.
}

ENV_LABELS = {
    "jetson-nano": "Jetson\nNano",
    "jetson-orin": "Jetson AGX\nOrin",
    "desktop-legion": "Desktop\nLegion",
}


def plot_latency_distribution(loader: BenchmarkLoader, output_dir: Path) -> None:
    """Generate a latency distribution boxplot grouped by environment."""
    output_dir.mkdir(parents=True, exist_ok=True)

    # Group SLM latency values by environment.
    env_latencies: Dict[str, List[float]] = {}

    for record in loader.data:
        environment = record["environment"]
        env_latencies.setdefault(environment, []).append(record["slm_per_diagnosis_s"])

    envs = sorted(env_latencies.keys())
    data_to_plot = [env_latencies[env] for env in envs]
    tick_labels = [ENV_LABELS.get(env, env.replace("-", "\n")) for env in envs]

    fig, ax = plt.subplots(figsize=(11, 6.5))

    boxplot = ax.boxplot(
        data_to_plot,
        tick_labels=tick_labels,
        patch_artist=True,
        notch=True,
        showmeans=True,
        meanprops={
            "marker": "D",
            "markerfacecolor": "red",
            "markeredgecolor": "black",
            "markersize": 6,
        },
    )

    # Apply colors to boxes.
    for patch, env in zip(boxplot["boxes"], envs):
        patch.set_facecolor(ENV_COLORS.get(env, "#3D3D3D"))
        patch.set_alpha(0.75)
        patch.set_linewidth(1.5)

    # Style whiskers, medians, caps, and fliers.
    for whisker in boxplot["whiskers"]:
        whisker.set(linewidth=1.5, color="#333333")

    for cap in boxplot["caps"]:
        cap.set(linewidth=1.5, color="#333333")

    for median in boxplot["medians"]:
        median.set(linewidth=2, color="#000000")

    for flier in boxplot["fliers"]:
        flier.set(marker="o", markersize=4, markerfacecolor="white", markeredgecolor="#333333")

    ax.axhline(
        y=1.0,
        color="#C41E3A",
        linestyle="--",
        linewidth=2.5,
        label="Target (1.0s)",
        alpha=0.8,
    )

    ax.set_ylabel("SLM Latency (s)", fontsize=12, fontweight="bold")
    ax.set_title(
        "SLM Latency Distribution by Environment\n"
        "(boxplot: median, quartiles, mean, and outliers)",
        fontsize=13,
        fontweight="bold",
        pad=15,
    )

    ax.legend(fontsize=11, loc="upper right")
    ax.grid(axis="y", alpha=0.25, linestyle=":", linewidth=0.8)
    ax.set_ylim(bottom=0)
    ax.spines[["top", "right"]].set_visible(False)

    # Add a compact statistics footer.
    stats_text = "Statistics by Environment:"

    for env in envs:
        values = env_latencies[env]

        min_val = np.min(values)
        max_val = np.max(values)
        median_val = np.median(values)
        mean_val = np.mean(values)
        std_val = np.std(values)

        stats_text += (
            f"\n  {env}: mean={mean_val:.3f}s +/- {std_val:.3f}s"
            f" | median={median_val:.3f}s"
            f" | range=[{min_val:.3f}, {max_val:.3f}]s"
        )

    fig.text(
        0.5,
        -0.05,
        stats_text,
        ha="center",
        fontsize=9,
        family="monospace",
        bbox={
            "boxstyle": "round,pad=0.8",
            "facecolor": "#F5F5F5",
            "edgecolor": "#999999",
            "alpha": 0.8,
        },
    )

    plt.tight_layout()
    plt.subplots_adjust(bottom=0.25)

    output_file = output_dir / "04_latency_distribution.png"
    plt.savefig(output_file, dpi=300, bbox_inches="tight")
    plt.close(fig)

    print(f"Saved: {output_file}")


if __name__ == "__main__":
    project_root = SCRIPT_DIR.parent.parent
    loader = BenchmarkLoader(project_root / "outputs")
    plot_latency_distribution(loader, SCRIPT_DIR.parent / "plots_output")