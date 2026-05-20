"""
Plot 10: Qwen CPU vs GPU on Jetson Nano.

Compares Qwen latency, throughput, and target success rate between CPU and GPU
execution on Jetson Nano.

Generated files:
- 10_qwen_nano_latency_cpu_vs_gpu.png
- 10_qwen_nano_throughput_cpu_vs_gpu.png
- 10_qwen_nano_success_cpu_vs_gpu.png
"""

import sys
from pathlib import Path
from statistics import mean
from typing import Dict, List

import matplotlib.pyplot as plt
import numpy as np

# Allow importing local plotting utilities when running from the project root.
SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from data_loader import BenchmarkLoader


# Jetson Nano orange palette: lighter for CPU, more saturated for GPU.
COLORS = {
    "cpu": "#FFCC80",
    "gpu": "#FF9800",
}

LABELS = {
    "cpu": "Qwen CPU",
    "gpu": "Qwen GPU",
}

TARGET_LINE = {
    "color": "#E53935",
    "linestyle": "--",
    "linewidth": 1.6,
}


def _filter_qwen_nano(loader: BenchmarkLoader) -> Dict[str, List[dict]]:
    """Return summary rows grouped as 'cpu' and 'gpu' for Jetson Nano Qwen."""
    variants: Dict[str, List[dict]] = {}

    for row in loader.summary_by_env_model():
        if row["environment"] != "jetson-nano":
            continue

        model = row["model"].lower()

        if "qwen" not in model:
            continue

        key = "cpu" if "cpu" in model else "gpu"
        variants.setdefault(key, []).append(row)

    return variants


def _filter_qwen_nano_raw(loader: BenchmarkLoader) -> Dict[str, List[dict]]:
    """Return raw benchmark records grouped as 'cpu' and 'gpu'."""
    variants: Dict[str, List[dict]] = {}

    for record in loader.data:
        if record["environment"] != "jetson-nano":
            continue

        model = record["model"].lower()

        if "qwen" not in model:
            continue

        key = "cpu" if "cpu" in model else "gpu"
        variants.setdefault(key, []).append(record)

    return variants


def _base_bar_chart(
    keys: List[str],
    values: List[float],
    colors: List[str],
    title: str,
    ylabel: str,
    target_value: float,
    target_label: str,
    errors: List[float] = None,
):
    """Create a base bar chart with target line, labels, and optional error bars."""
    fig, ax = plt.subplots(figsize=(7, 5))
    x = np.arange(len(keys))

    bars = ax.bar(
        x,
        values,
        color=colors,
        alpha=0.88,
        edgecolor="white",
        linewidth=1.2,
        width=0.45,
    )

    if errors:
        for idx, (value, error) in enumerate(zip(values, errors)):
            ax.errorbar(
                idx,
                value,
                yerr=error,
                fmt="none",
                ecolor="#555555",
                elinewidth=1.4,
                capsize=5,
                capthick=1.4,
            )

    ax.axhline(target_value, label=target_label, **TARGET_LINE)
    ax.set_xticks(x)
    ax.set_xticklabels([LABELS[key] for key in keys], fontsize=11)
    ax.set_ylabel(ylabel, fontsize=12, fontweight="bold")
    ax.set_title(title, fontsize=13, fontweight="bold")
    ax.set_ylim(bottom=0)
    ax.legend(fontsize=11)
    ax.grid(axis="y", alpha=0.25)
    ax.spines[["top", "right"]].set_visible(False)

    return fig, ax, bars


def plot_qwen_nano_latency(loader: BenchmarkLoader, output_dir: Path) -> None:
    """Generate the Qwen CPU vs GPU latency plot for Jetson Nano."""
    output_dir.mkdir(parents=True, exist_ok=True)

    variants = _filter_qwen_nano(loader)

    if not variants:
        print("No Qwen data found for Jetson Nano.")
        return

    keys = [key for key in ("cpu", "gpu") if key in variants]
    latencies = [mean(row["slm_per_diag_mean"] for row in variants[key]) for key in keys]
    errors = [mean(row["slm_per_diag_std"] for row in variants[key]) for key in keys]
    colors = [COLORS[key] for key in keys]

    fig, ax, bars = _base_bar_chart(
        keys,
        latencies,
        colors,
        title="Jetson Nano: Qwen CPU vs GPU Latency\n(lower = better)",
        ylabel="Latency (s)",
        target_value=1.0,
        target_label="Target (1.0 s)",
        errors=errors,
    )

    for bar, latency, error in zip(bars, latencies, errors):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            latency + error + 0.05,
            f"{latency:.3f}s",
            ha="center",
            va="bottom",
            fontsize=11,
            fontweight="bold",
        )

    # Speedup annotation, available when both CPU and GPU data are present.
    if len(keys) == 2 and keys == ["cpu", "gpu"]:
        speedup = latencies[0] / latencies[1]

        ax.annotate(
            f"GPU Speedup: {speedup:.1f}x",
            xy=(1, latencies[1]),
            xytext=(0.5, latencies[0] * 0.6),
            fontsize=12,
            fontweight="bold",
            ha="center",
            arrowprops={
                "arrowstyle": "->",
                "color": "#333333",
                "lw": 1.2,
            },
            bbox={
                "boxstyle": "round,pad=0.4",
                "facecolor": "#FFF9C4",
                "alpha": 0.9,
            },
        )

    plt.tight_layout()

    output_file = output_dir / "10_qwen_nano_latency_cpu_vs_gpu.png"
    plt.savefig(output_file, dpi=300, bbox_inches="tight")
    plt.close(fig)

    print(f"Saved: {output_file}")


def plot_qwen_nano_throughput(loader: BenchmarkLoader, output_dir: Path) -> None:
    """Generate the Qwen CPU vs GPU throughput plot for Jetson Nano."""
    output_dir.mkdir(parents=True, exist_ok=True)

    variants = _filter_qwen_nano(loader)

    if not variants:
        print("No Qwen data found for Jetson Nano.")
        return

    keys = [key for key in ("cpu", "gpu") if key in variants]
    throughputs = [
        1.0 / mean(row["slm_per_diag_mean"] for row in variants[key])
        for key in keys
    ]
    colors = [COLORS[key] for key in keys]

    fig, ax, bars = _base_bar_chart(
        keys,
        throughputs,
        colors,
        title="Jetson Nano: Qwen CPU vs GPU Throughput\n(higher = better)",
        ylabel="Throughput (diagnoses/s)",
        target_value=1.0,
        target_label="Target (1.0 diag/s)",
    )

    for bar, throughput in zip(bars, throughputs):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            throughput + 0.03,
            f"{throughput:.2f}",
            ha="center",
            va="bottom",
            fontsize=11,
            fontweight="bold",
        )

    plt.tight_layout()

    output_file = output_dir / "10_qwen_nano_throughput_cpu_vs_gpu.png"
    plt.savefig(output_file, dpi=300, bbox_inches="tight")
    plt.close(fig)

    print(f"Saved: {output_file}")


def plot_qwen_nano_success(loader: BenchmarkLoader, output_dir: Path) -> None:
    """Generate the Qwen CPU vs GPU target success-rate plot for Jetson Nano."""
    output_dir.mkdir(parents=True, exist_ok=True)

    raw = _filter_qwen_nano_raw(loader)

    if not raw:
        print("No Qwen data found for Jetson Nano.")
        return

    keys = [key for key in ("cpu", "gpu") if key in raw]
    success_rates = []
    counts = []
    totals = []

    for key in keys:
        records = raw[key]
        hits = sum(1 for record in records if record["slm_per_diagnosis_s"] <= 1.0)
        total = len(records)

        success_rates.append(hits / max(1, total) * 100)
        counts.append(hits)
        totals.append(total)

    colors = [COLORS[key] for key in keys]

    fig, ax, bars = _base_bar_chart(
        keys,
        success_rates,
        colors,
        title="Jetson Nano: Qwen CPU vs GPU Target Met Rate\n(higher = better)",
        ylabel="Target Success Rate (%)",
        target_value=100.0,
        target_label="Target (100%)",
    )

    ax.set_ylim(0, 118)

    for bar, rate, count, total in zip(bars, success_rates, counts, totals):
        # Percentage above the bar.
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            rate + 3,
            f"{rate:.1f}%",
            ha="center",
            va="bottom",
            fontsize=12,
            fontweight="bold",
        )

        # Count inside the bar.
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            rate / 2,
            f"{count}/{total}",
            ha="center",
            va="center",
            fontsize=11,
            fontweight="bold",
            color="white",
            bbox={
                "boxstyle": "round,pad=0.3",
                "facecolor": "#333333",
                "alpha": 0.7,
            },
        )

    plt.tight_layout()

    output_file = output_dir / "10_qwen_nano_success_cpu_vs_gpu.png"
    plt.savefig(output_file, dpi=300, bbox_inches="tight")
    plt.close(fig)

    print(f"Saved: {output_file}")


def plot_qwen_cpu_vs_gpu(loader: BenchmarkLoader, output_dir: Path) -> None:
    """Generate all Qwen CPU vs GPU plots for Jetson Nano."""
    plot_qwen_nano_latency(loader, output_dir)
    plot_qwen_nano_throughput(loader, output_dir)
    plot_qwen_nano_success(loader, output_dir)


if __name__ == "__main__":
    project_root = SCRIPT_DIR.parent.parent
    loader = BenchmarkLoader(project_root / "outputs")
    plot_qwen_cpu_vs_gpu(loader, SCRIPT_DIR.parent / "plots_output")