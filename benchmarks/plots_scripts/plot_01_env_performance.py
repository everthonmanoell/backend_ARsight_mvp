"""
Plot 1 (Figura 6): SLM Latency e Throughput por plataforma
- 01_env_latency.png
- 01_env_throughput.png
"""

import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
from data_loader import BenchmarkLoader
from statistics import mean


PLATFORM_COLORS = {
    "desktop-legion": "#2196F3",
    "jetson-nano":    "#FF9800",
    "jetson-orin":    "#4CAF50",
}

PLATFORM_LABELS = {
    "desktop-legion": "Desktop Legion",
    "jetson-nano":    "Jetson Nano",
    "jetson-orin":    "Jetson AGX Orin",
}


def _aggregate_by_env(loader: BenchmarkLoader) -> dict[str, list[float]]:
    """Retorna latências médias agrupadas por environment."""
    env_data: dict[str, list] = {}
    for row in loader.summary_by_env_model():
        env_data.setdefault(row["environment"], []).append(row["slm_per_diag_mean"])
    return env_data


def plot_env_latency(loader: BenchmarkLoader, output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)

    env_data = _aggregate_by_env(loader)
    envs     = sorted(env_data.keys())
    latencies = [mean(env_data[e]) for e in envs]
    labels    = [PLATFORM_LABELS.get(e, e) for e in envs]
    colors    = [PLATFORM_COLORS.get(e, "#999999") for e in envs]

    fig, ax = plt.subplots(figsize=(8, 5))

    bars = ax.bar(labels, latencies, color=colors, alpha=0.85,
                  edgecolor="white", linewidth=1.2, width=0.5)

    ax.axhline(1.0, color="#E53935", linestyle="--", linewidth=1.6,
               label="Target (1.0s)")

    # Rótulos de valor
    for bar, lat in zip(bars, latencies):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 0.08,
            f"{lat:.3f}s",
            ha="center", va="bottom", fontsize=11, fontweight="bold"
        )

    ax.set_ylabel("Latency (s)", fontsize=12, fontweight="bold")
    ax.set_title("SLM Latency by Environment\n(lower = better)",
                 fontsize=13, fontweight="bold")
    ax.set_ylim(bottom=0)
    ax.legend(fontsize=11)
    ax.grid(axis="y", alpha=0.25)
    ax.spines[["top", "right"]].set_visible(False)

    plt.tight_layout()
    out = output_dir / "01_env_latency.png"
    plt.savefig(out, dpi=300, bbox_inches="tight")
    print(f"✅ Saved: {out}")
    plt.close()


def plot_env_throughput(loader: BenchmarkLoader, output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)

    env_data    = _aggregate_by_env(loader)
    envs        = sorted(env_data.keys())
    throughputs = [1.0 / mean(env_data[e]) for e in envs]
    labels      = [PLATFORM_LABELS.get(e, e) for e in envs]
    colors      = [PLATFORM_COLORS.get(e, "#999999") for e in envs]

    fig, ax = plt.subplots(figsize=(8, 5))

    bars = ax.bar(labels, throughputs, color=colors, alpha=0.85,
                  edgecolor="white", linewidth=1.2, width=0.5)

    ax.axhline(1.0, color="#E53935", linestyle="--", linewidth=1.6,
               label="Target (1.0 diag/s)")

    # Rótulos de valor
    for bar, tp in zip(bars, throughputs):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 0.04,
            f"{tp:.2f}",
            ha="center", va="bottom", fontsize=11, fontweight="bold"
        )

    ax.set_ylabel("Throughput (diagnoses/s)", fontsize=12, fontweight="bold")
    ax.set_title("Throughput by Environment\n(higher = better)",
                 fontsize=13, fontweight="bold")
    ax.set_ylim(bottom=0)
    ax.legend(fontsize=11)
    ax.grid(axis="y", alpha=0.25)
    ax.spines[["top", "right"]].set_visible(False)

    plt.tight_layout()
    out = output_dir / "01_env_throughput.png"
    plt.savefig(out, dpi=300, bbox_inches="tight")
    print(f"✅ Saved: {out}")
    plt.close()


def plot_env_performance(loader: BenchmarkLoader, output_dir: Path) -> None:
    plot_env_latency(loader, output_dir)
    plot_env_throughput(loader, output_dir)


if __name__ == "__main__":
    loader = BenchmarkLoader(Path("../../outputs"))
    plot_env_performance(loader, Path("./"))