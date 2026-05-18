"""
Plot 7: Jetson Nano Performance by Model - SEPARATED INTO THREE PLOT FILES
- Latency (07_jetson_nano_latency.png)
- Throughput (07_jetson_nano_throughput.png)
- Target Success Rate (07_jetson_nano_success.png)

Includes Qwen CPU variant when available
"""

import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
from data_loader import BenchmarkLoader


# Color palette by model
PALETTE = {
    "dialogpt": {"face": "#D7F8D7", "edge": "#000000", "label": "DialoGPT"},
    "phi":      {"face": "#9FE1CB", "edge": "#000000", "label": "Phi"},
    "qwen":     {"face": "#518A58", "edge": "#000000", "label": "Qwen GPU"},
    "qwen-gpu": {"face": "#0C4D0C", "edge": "#000000", "label": "Qwen GPU"},
    "qwen-cpu": {"face": "#3CFD35", "edge": "#000000", "label": "Qwen CPU"},
}


def plot_jetson_nano_latency(loader: BenchmarkLoader, output_dir: Path) -> None:
    """Latency chart for Jetson Nano by model"""
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    summary = loader.summary_by_env_model()
    
    # Filter only Jetson Nano data
    nano_data = {}
    for row in summary:
        if row["environment"] == "jetson-nano":
            model = row["model"].lower()
            nano_data[model] = row
    
    if not nano_data:
        print("  ⚠️  No Jetson Nano data found")
        return
    
    # Exclude CPU-only for this main comparison (unless only CPU available)
    display_models = [m for m in sorted(nano_data.keys()) if not m.endswith("-cpu") or len(nano_data) == 1]
    if not display_models:
        display_models = sorted(nano_data.keys())
    
    model_labels = [PALETTE.get(m, {}).get("label", m) for m in display_models]
    x = np.arange(len(display_models))
    
    face_colors = [PALETTE.get(m, {}).get("face", "#999") for m in display_models]
    edge_colors = [PALETTE.get(m, {}).get("edge", "#333") for m in display_models]
    
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Latency
    latencies = [nano_data[model]["slm_per_diag_mean"] for model in display_models]
    errors = [nano_data[model]["slm_per_diag_std"] for model in display_models]
    
    bars = ax.bar(x, latencies, color=face_colors, edgecolor=edge_colors, linewidth=1.5, width=0.6, alpha=0.8)
    
    # Error bars
    for i, (bar, lat, err, ec) in enumerate(zip(bars, latencies, errors, edge_colors)):
        ax.errorbar(i, lat, yerr=err, fmt='none', ecolor=ec, elinewidth=1.5, capsize=5, capthick=1.5, zorder=3)
    
    ax.axhline(y=1.0, color="#E24B4A", linestyle="--", linewidth=2, label="Target (1.0s)", zorder=4)
    ax.set_xticks(x)
    ax.set_xticklabels(model_labels, fontsize=11)
    ax.set_ylim(0, max(latencies) * 1.3)
    ax.set_ylabel("Latency (s)", fontsize=12, fontweight="bold")
    ax.set_title("Jetson Nano: SLM Latency by Model\n(lower = better)", fontsize=13, fontweight="bold", pad=15)
    ax.grid(axis="y", alpha=0.3)
    ax.legend(fontsize=11, frameon=False)
    
    for i, (bar, val, err) in enumerate(zip(bars, latencies, errors)):
        ax.text(bar.get_x() + bar.get_width() / 2, val + err + 0.1,
                f"{val:.3f}s", ha="center", va="bottom", fontsize=11, fontweight="bold")
    
    plt.tight_layout()
    output_file = output_dir / "07_jetson_nano_latency.png"
    plt.savefig(output_file, dpi=300, bbox_inches="tight")
    print(f"✅ Saved: {output_file}")
    plt.close()


def plot_jetson_nano_throughput(loader: BenchmarkLoader, output_dir: Path) -> None:
    """Throughput chart for Jetson Nano by model"""
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    summary = loader.summary_by_env_model()
    
    # Filter only Jetson Nano data
    nano_data = {}
    for row in summary:
        if row["environment"] == "jetson-nano":
            model = row["model"].lower()
            nano_data[model] = row
    
    if not nano_data:
        return
    
    display_models = [m for m in sorted(nano_data.keys()) if not m.endswith("-cpu") or len(nano_data) == 1]
    if not display_models:
        display_models = sorted(nano_data.keys())
    
    model_labels = [PALETTE.get(m, {}).get("label", m) for m in display_models]
    x = np.arange(len(display_models))
    
    face_colors = [PALETTE.get(m, {}).get("face", "#999") for m in display_models]
    edge_colors = [PALETTE.get(m, {}).get("edge", "#333") for m in display_models]
    
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Throughput
    throughputs = [1.0 / nano_data[model]["slm_per_diag_mean"] for model in display_models]
    
    bars = ax.bar(x, throughputs, color=face_colors, edgecolor=edge_colors, linewidth=1.5, width=0.6, alpha=0.8)
    
    ax.axhline(y=1.0, color="#22C55E", linestyle="--", linewidth=2, label="Target (1.0 diag/s)", zorder=4)
    ax.set_xticks(x)
    ax.set_xticklabels(model_labels, fontsize=11)
    ax.set_ylim(0, max(throughputs) * 1.3)
    ax.set_ylabel("Throughput (diagnoses/s)", fontsize=12, fontweight="bold")
    ax.set_title("Jetson Nano: Throughput by Model\n(higher = better)", fontsize=13, fontweight="bold", pad=15)
    ax.grid(axis="y", alpha=0.3)
    ax.legend(fontsize=11, frameon=False)
    
    for bar, val in zip(bars, throughputs):
        ax.text(bar.get_x() + bar.get_width() / 2, val + 0.05,
                f"{val:.2f}", ha="center", va="bottom", fontsize=11, fontweight="bold")
    
    plt.tight_layout()
    output_file = output_dir / "07_jetson_nano_throughput.png"
    plt.savefig(output_file, dpi=300, bbox_inches="tight")
    print(f"✅ Saved: {output_file}")
    plt.close()


def plot_jetson_nano_success(loader: BenchmarkLoader, output_dir: Path) -> None:
    """Target success rate chart for Jetson Nano by model"""
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Calculate target success rate for each model
    target_rates = {}
    for record in loader.data:
        if record["environment"] == "jetson-nano":
            model = record["model"].lower()
            if model not in target_rates:
                target_rates[model] = {"success": 0, "total": 0}
            target_rates[model]["total"] += 1
            if record["slm_per_diagnosis_s"] <= 1.0:
                target_rates[model]["success"] += 1
    
    if not target_rates:
        return
    
    display_models = [m for m in sorted(target_rates.keys()) if not m.endswith("-cpu") or len(target_rates) == 1]
    if not display_models:
        display_models = sorted(target_rates.keys())
    
    model_labels = [PALETTE.get(m, {}).get("label", m) for m in display_models]
    x = np.arange(len(display_models))
    
    face_colors = [PALETTE.get(m, {}).get("face", "#999") for m in display_models]
    edge_colors = [PALETTE.get(m, {}).get("edge", "#333") for m in display_models]
    
    fig, ax = plt.subplots(figsize=(10, 6))
    
    success_rates = []
    for model in display_models:
        rate = target_rates[model]["success"] / max(1, target_rates[model]["total"]) * 100
        success_rates.append(rate)
    
    bars = ax.bar(x, success_rates, color=face_colors, edgecolor=edge_colors, linewidth=1.5, width=0.6, alpha=0.8)
    
    ax.axhline(y=100.0, color="#22C55E", linestyle="--", linewidth=2, label="Target (100%)", zorder=4)
    ax.set_xticks(x)
    ax.set_xticklabels(model_labels, fontsize=11)
    ax.set_ylim(0, 110)
    ax.set_ylabel("Target Success Rate (%)", fontsize=12, fontweight="bold")
    ax.set_title("Jetson Nano: Target Met Rate by Model\n(higher = better)", fontsize=13, fontweight="bold", pad=15)
    ax.grid(axis="y", alpha=0.3)
    ax.legend(fontsize=11, frameon=False)
    
    for i, (bar, rate, model) in enumerate(zip(bars, success_rates, display_models)):
        count = target_rates[model]["success"]
        total = target_rates[model]["total"]
        ax.text(bar.get_x() + bar.get_width() / 2, rate + 2,
                f"{rate:.1f}%\n({count}/{total})", ha="center", va="bottom", fontsize=10, fontweight="bold")
    
    plt.tight_layout()
    output_file = output_dir / "07_jetson_nano_success.png"
    plt.savefig(output_file, dpi=300, bbox_inches="tight")
    print(f"✅ Saved: {output_file}")
    plt.close()


def plot_jetson_nano(loader: BenchmarkLoader, output_dir: Path) -> None:
    """Wrapper function that calls all three separated plots"""
    plot_jetson_nano_latency(loader, output_dir)
    plot_jetson_nano_throughput(loader, output_dir)
    plot_jetson_nano_success(loader, output_dir)


if __name__ == "__main__":
    loader = BenchmarkLoader(Path("../../outputs"))
    plot_jetson_nano(loader, Path("./"))
