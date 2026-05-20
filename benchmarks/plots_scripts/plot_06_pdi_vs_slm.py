"""
Plot 6: PDI vs SLM processing time.

Compares deterministic computer vision processing time against SLM inference
time across environments and models.

Generated file:
- 06_pdi_vs_slm.png
"""

import sys
from pathlib import Path
from statistics import mean
from typing import Dict, List, Tuple

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np

# Allow importing local plotting utilities when running from the project root.
SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from data_loader import BenchmarkLoader


PLATFORM_COLORS = {
    "desktop-legion": "#2196F3",   # Blue.
    "jetson-nano": "#FF9800",      # Orange.
    "jetson-orin": "#4CAF50",      # Green.
}

PLATFORM_LABELS = {
    "desktop-legion": "Desktop Legion",
    "jetson-nano": "Jetson Nano",
    "jetson-orin": "Jetson AGX Orin",
}


def plot_slm_vs_pdi(loader: BenchmarkLoader, output_dir: Path) -> None:
    """Generate a log-scale comparison between PDI and SLM processing time."""
    output_dir.mkdir(parents=True, exist_ok=True)

    env_model_times: Dict[Tuple[str, str], Dict[str, List[float]]] = {}

    for record in loader.data:
        key = (record["environment"], record["model"])

        env_model_times.setdefault(key, {"pdi": [], "slm": []})
        env_model_times[key]["pdi"].append(record["pdi_per_image_ms"])
        env_model_times[key]["slm"].append(record["slm_per_diagnosis_s"] * 1000)

    # Sort entries to group bars by platform and model.
    sorted_keys = sorted(env_model_times.keys(), key=lambda key: (key[0], key[1]))

    labels = []
    pdi_means = []
    slm_means = []
    colors = []

    for env, model in sorted_keys:
        times = env_model_times[(env, model)]

        labels.append(model)
        pdi_means.append(mean(times["pdi"]))
        slm_means.append(mean(times["slm"]))
        colors.append(PLATFORM_COLORS.get(env, "#999999"))

    x = np.arange(len(labels))
    width = 0.35

    fig, ax = plt.subplots(figsize=(15, 7))

    bars_pdi = ax.bar(
        x - width / 2,
        pdi_means,
        width,
        color=colors,
        alpha=0.55,
        hatch="///",
        edgecolor="white",
        linewidth=0.8,
        label="_nolegend_",
    )

    bars_slm = ax.bar(
        x + width / 2,
        slm_means,
        width,
        color=colors,
        alpha=0.92,
        edgecolor="white",
        linewidth=0.8,
        label="_nolegend_",
    )

    # Log scale is required because PDI and SLM operate on very different time scales.
    ax.set_yscale("log")
    ax.set_ylim(bottom=5)

    # Reference line: 1000 ms = 1 s latency target.
    ax.axhline(
        1000,
        color="#E53935",
        linestyle="--",
        linewidth=1.4,
        label="Target (1.0 s)",
    )

    # Value labels above bars.
    for bar in list(bars_pdi) + list(bars_slm):
        height = bar.get_height()
        label_text = f"{height:.0f}" if height >= 10 else f"{height:.1f}"

        ax.text(
            bar.get_x() + bar.get_width() / 2,
            height * 1.15,
            label_text,
            ha="center",
            va="bottom",
            fontsize=8,
            fontweight="bold",
        )

    # Vertical separators between platforms.
    platforms = [key[0] for key in sorted_keys]

    for idx in range(1, len(platforms)):
        if platforms[idx] != platforms[idx - 1]:
            ax.axvline(
                idx - 0.5,
                color="#CCCCCC",
                linestyle="-",
                linewidth=1.2,
            )

    # Platform labels at the top of the plot.
    platform_groups: Dict[str, List[int]] = {}

    for idx, (env, _) in enumerate(sorted_keys):
        platform_groups.setdefault(env, []).append(idx)

    ax_top = ax.secondary_xaxis("top")
    ax_top.set_xlim(ax.get_xlim())
    ax_top.set_xticks([np.mean(indices) for indices in platform_groups.values()])
    ax_top.set_xticklabels(
        [PLATFORM_LABELS.get(env, env) for env in platform_groups],
        fontsize=11,
        fontweight="bold",
    )
    ax_top.tick_params(length=0)

    ax.set_ylabel("Time (ms) — log scale", fontsize=12, fontweight="bold")
    ax.set_title(
        "PDI vs SLM Processing Time by Environment and Model\n"
        "(which component is the bottleneck?)",
        fontsize=13,
        fontweight="bold",
        pad=28,
    )

    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=10)
    ax.grid(axis="y", alpha=0.25, which="both")
    ax.spines[["top", "right"]].set_visible(False)

    # Legend: platform colors and processing-stage styles.
    platform_patches = [
        mpatches.Patch(color=color, label=PLATFORM_LABELS[env])
        for env, color in PLATFORM_COLORS.items()
    ]

    style_patches = [
        mpatches.Patch(
            facecolor="#999999",
            hatch="///",
            edgecolor="white",
            alpha=0.55,
            label="PDI (Computer Vision)",
        ),
        mpatches.Patch(
            facecolor="#999999",
            edgecolor="white",
            alpha=0.92,
            label="SLM (Language Model)",
        ),
    ]

    target_line = plt.Line2D(
        [0],
        [0],
        color="#E53935",
        linestyle="--",
        linewidth=1.4,
        label="Target (1.0 s)",
    )

    ax.legend(
        handles=platform_patches + [target_line] + style_patches,
        fontsize=10,
        loc="upper left",
        framealpha=0.9,
    )

    plt.tight_layout()

    output_file = output_dir / "06_pdi_vs_slm.png"
    plt.savefig(output_file, dpi=300, bbox_inches="tight")
    plt.close(fig)

    print(f"Saved: {output_file}")


if __name__ == "__main__":
    project_root = SCRIPT_DIR.parent.parent
    loader = BenchmarkLoader(project_root / "outputs")
    plot_slm_vs_pdi(loader, SCRIPT_DIR.parent / "plots_output")