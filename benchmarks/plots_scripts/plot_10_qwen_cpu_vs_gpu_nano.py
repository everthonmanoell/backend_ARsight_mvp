"""
Plot 10 (Figura 8): Qwen CPU vs GPU no Jetson Nano
- 10_qwen_nano_latency_cpu_vs_gpu.png
- 10_qwen_nano_throughput_cpu_vs_gpu.png
- 10_qwen_nano_success_cpu_vs_gpu.png
"""

import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
from data_loader import BenchmarkLoader
from statistics import mean

# Laranja Jetson Nano: CPU mais claro, GPU mais saturado
COLORS = {
    "cpu": "#FFCC80",   
    "gpu": "#FF9800",    
}

LABELS = {
    "cpu": "Qwen CPU",
    "gpu": "Qwen GPU",
}

TARGET_LINE = {"color": "#E53935", "linestyle": "--", "linewidth": 1.6}


def _filter_qwen_nano(loader: BenchmarkLoader) -> dict[str, list]:
    """Retorna summary rows agrupados em 'cpu' e 'gpu' para Jetson Nano / Qwen."""
    variants: dict[str, list] = {}
    for row in loader.summary_by_env_model():
        if row["environment"] != "jetson-nano":
            continue
        model = row["model"].lower()
        if "qwen" not in model:
            continue
        key = "cpu" if "cpu" in model else "gpu"
        variants.setdefault(key, []).append(row)
    return variants


def _filter_qwen_nano_raw(loader: BenchmarkLoader) -> dict[str, list]:
    """Retorna registros brutos agrupados em 'cpu' e 'gpu'."""
    variants: dict[str, list] = {}
    for record in loader.data:
        if record["environment"] != "jetson-nano":
            continue
        if "qwen" not in record["model"].lower():
            continue
        key = "cpu" if "cpu" in record["model"].lower() else "gpu"
        variants.setdefault(key, []).append(record)
    return variants


def _base_bar_chart(keys, values, colors, title, ylabel,
                    target_val, target_label, errors=None):
    """Monta figura base com barras, linha de target e labels."""
    fig, ax = plt.subplots(figsize=(7, 5))
    x = np.arange(len(keys))

    bars = ax.bar(x, values, color=colors, alpha=0.88,
                  edgecolor="white", linewidth=1.2, width=0.45)

    if errors:
        for i, (v, e) in enumerate(zip(values, errors)):
            ax.errorbar(i, v, yerr=e, fmt="none",
                        ecolor="#555", elinewidth=1.4, capsize=5, capthick=1.4)

    ax.axhline(target_val, label=target_label, **TARGET_LINE)
    ax.set_xticks(x)
    ax.set_xticklabels([LABELS[k] for k in keys], fontsize=11)
    ax.set_ylabel(ylabel, fontsize=12, fontweight="bold")
    ax.set_title(title, fontsize=13, fontweight="bold")
    ax.set_ylim(bottom=0)
    ax.legend(fontsize=11)
    ax.grid(axis="y", alpha=0.25)
    ax.spines[["top", "right"]].set_visible(False)

    return fig, ax, bars


def plot_qwen_nano_latency(loader: BenchmarkLoader, output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    variants = _filter_qwen_nano(loader)
    if not variants:
        print("  ⚠️  No Qwen data for Jetson Nano")
        return

    keys = [k for k in ("cpu", "gpu") if k in variants]
    latencies = [mean(r["slm_per_diag_mean"] for r in variants[k]) for k in keys]
    errors    = [mean(r["slm_per_diag_std"]  for r in variants[k]) for k in keys]
    colors    = [COLORS[k] for k in keys]

    fig, ax, bars = _base_bar_chart(
        keys, latencies, colors,
        title="Jetson Nano: Qwen CPU vs GPU Latency\n(lower = better)",
        ylabel="Latency (s)",
        target_val=1.0, target_label="Target (1.0 s)",
        errors=errors,
    )

    for bar, lat, err in zip(bars, latencies, errors):
        ax.text(bar.get_x() + bar.get_width() / 2,
                lat + err + 0.05,
                f"{lat:.3f}s",
                ha="center", va="bottom", fontsize=11, fontweight="bold")

    # Speedup annotation
    if len(latencies) == 2:
        speedup = latencies[0] / latencies[1]
        ax.annotate(
            f"GPU Speedup: {speedup:.1f}×",
            xy=(1, latencies[1]),
            xytext=(0.5, latencies[0] * 0.6),
            fontsize=12, fontweight="bold", ha="center",
            arrowprops=dict(arrowstyle="->", color="#333", lw=1.2),
            bbox=dict(boxstyle="round,pad=0.4", facecolor="#FFF9C4", alpha=0.9),
        )

    plt.tight_layout()
    out = output_dir / "10_qwen_nano_latency_cpu_vs_gpu.png"
    plt.savefig(out, dpi=300, bbox_inches="tight")
    print(f"✅ Saved: {out}")
    plt.close()


def plot_qwen_nano_throughput(loader: BenchmarkLoader, output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    variants = _filter_qwen_nano(loader)
    if not variants:
        return

    keys        = [k for k in ("cpu", "gpu") if k in variants]
    throughputs = [1.0 / mean(r["slm_per_diag_mean"] for r in variants[k]) for k in keys]
    colors      = [COLORS[k] for k in keys]

    fig, ax, bars = _base_bar_chart(
        keys, throughputs, colors,
        title="Jetson Nano: Qwen CPU vs GPU Throughput\n(higher = better)",
        ylabel="Throughput (diagnoses/s)",
        target_val=1.0, target_label="Target (1.0 diag/s)",
    )

    for bar, tp in zip(bars, throughputs):
        ax.text(bar.get_x() + bar.get_width() / 2,
                tp + 0.03,
                f"{tp:.2f}",
                ha="center", va="bottom", fontsize=11, fontweight="bold")

    plt.tight_layout()
    out = output_dir / "10_qwen_nano_throughput_cpu_vs_gpu.png"
    plt.savefig(out, dpi=300, bbox_inches="tight")
    print(f"✅ Saved: {out}")
    plt.close()


def plot_qwen_nano_success(loader: BenchmarkLoader, output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    raw = _filter_qwen_nano_raw(loader)
    if not raw:
        return

    keys = [k for k in ("cpu", "gpu") if k in raw]
    success_rates, counts, totals = [], [], []

    for k in keys:
        records = raw[k]
        hits    = sum(1 for r in records if r["slm_per_diagnosis_s"] <= 1.0)
        total   = len(records)
        success_rates.append(hits / max(1, total) * 100)
        counts.append(hits)
        totals.append(total)

    colors = [COLORS[k] for k in keys]

    fig, ax, bars = _base_bar_chart(
        keys, success_rates, colors,
        title="Jetson Nano: Qwen CPU vs GPU — Target Met Rate\n(higher = better)",
        ylabel="Target Success Rate (%)",
        target_val=100.0, target_label="Target (100%)",
    )
    ax.set_ylim(0, 118)

    for bar, rate, count, total in zip(bars, success_rates, counts, totals):
        # Percentual acima da barra
        ax.text(bar.get_x() + bar.get_width() / 2,
                rate + 3,
                f"{rate:.1f}%",
                ha="center", va="bottom", fontsize=12, fontweight="bold")
        # Contagem dentro da barra
        ax.text(bar.get_x() + bar.get_width() / 2,
                rate / 2,
                f"{count}/{total}",
                ha="center", va="center", fontsize=11, fontweight="bold",
                color="white",
                bbox=dict(boxstyle="round,pad=0.3", facecolor="#333", alpha=0.7))

    plt.tight_layout()
    out = output_dir / "10_qwen_nano_success_cpu_vs_gpu.png"
    plt.savefig(out, dpi=300, bbox_inches="tight")
    print(f"✅ Saved: {out}")
    plt.close()


def plot_qwen_cpu_vs_gpu(loader: BenchmarkLoader, output_dir: Path) -> None:
    plot_qwen_nano_latency(loader, output_dir)
    plot_qwen_nano_throughput(loader, output_dir)
    plot_qwen_nano_success(loader, output_dir)


if __name__ == "__main__":
    loader = BenchmarkLoader(Path("../../outputs"))
    plot_qwen_cpu_vs_gpu(loader, Path("./"))