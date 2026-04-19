"""
Plot 8: Jetson Orin Performance by Model
Professional design with custom colors and dual-axis metrics
"""

import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np
from pathlib import Path
from data_loader import BenchmarkLoader


# Color palette by model
PALETTE = {
    "dialogpt": {"face": "#B5D4F4", "edge": "#185FA5", "label": "DialoGPT"},
    "phi":      {"face": "#9FE1CB", "edge": "#0F6E56", "label": "Phi"},
    "qwen":     {"face": "#FAC775", "edge": "#854F0B", "label": "Qwen"},
}


def plot_jetson_orin(loader: BenchmarkLoader, output_dir: Path) -> None:
    """Creates professional performance chart for Jetson Orin by model"""
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    summary = loader.summary_by_env_model()
    
    # Filter only Jetson Orin data
    orin_data = {}
    for row in summary:
        if row["environment"] == "jetson-orin":
            model = row["model"].lower()
            orin_data[model] = row
    
    if not orin_data:
        print("  ⚠️  No Jetson Orin data found")
        return
    
    # Calculate target success rate for each model
    target_rates = {}
    for record in loader.data:
        if record["environment"] == "jetson-orin":
            model = record["model"].lower()
            if model not in target_rates:
                target_rates[model] = {"success": 0, "total": 0}
            target_rates[model]["total"] += 1
            if record["slm_per_diagnosis_s"] <= 1.0:
                target_rates[model]["success"] += 1
    
    models = sorted(orin_data.keys())
    model_labels = [PALETTE[m]["label"] for m in models]
    x = np.arange(len(models))
    
    face_colors = [PALETTE[m]["face"] for m in models]
    edge_colors = [PALETTE[m]["edge"] for m in models]
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6.5), gridspec_kw={"wspace": 0.35})
    
    # --- Panel 1: Latency ---
    latencies = [orin_data[model]["slm_per_diag_mean"] for model in models]
    errors = [orin_data[model]["slm_per_diag_std"] for model in models]
    
    bars1 = ax1.bar(x, latencies, color=face_colors, edgecolor=edge_colors, linewidth=1.5, width=0.5)
    
    # Draw error bars with per-model colors
    for i, (bar, lat, err, ec) in enumerate(zip(bars1, latencies, errors, edge_colors)):
        ax1.errorbar(i, lat, yerr=err, fmt='none', ecolor=ec, elinewidth=1.5, capsize=5, capthick=1.5, zorder=3)
    
    ax1.axhline(y=1.0, color="#E24B4A", linestyle="--", linewidth=1.8, label="Target (1.0s)", zorder=4)
    ax1.set_xticks(x)
    ax1.set_xticklabels(model_labels, fontsize=11)
    ax1.set_ylim(0, max(latencies) * 1.25)
    ax1.set_ylabel("Latency (s)", fontsize=12, fontweight="bold")
    ax1.set_title("Jetson Orin: SLM Latency\n(lower = better)", fontsize=12, fontweight="bold", pad=10)
    ax1.grid(axis="y", alpha=0.3)
    ax1.legend(fontsize=10, frameon=False)
    
    for i, (bar, val, err) in enumerate(zip(bars1, latencies, errors)):
        ax1.text(bar.get_x() + bar.get_width() / 2, val + err + 0.05,
                f"{val:.3f}s", ha="center", va="bottom", fontsize=10, fontweight="bold", color="#333")
    
    # --- Panel 2: Throughput + Success Rate ---
    throughputs = [1.0 / orin_data[model]["slm_per_diag_mean"] for model in models]
    success_rates = [target_rates.get(model, {"success": 0, "total": 1})["success"] / 
                    max(1, target_rates.get(model, {"success": 0, "total": 1})["total"]) * 100 
                    for model in models]
    
    bars2 = ax2.bar(x, throughputs, color=face_colors, edgecolor=edge_colors, linewidth=1.5, width=0.5)
    
    ax2.set_xticks(x)
    ax2.set_xticklabels(model_labels, fontsize=11)
    ax2.set_ylabel("Throughput (diag/s)", fontsize=12, fontweight="bold")
    ax2.set_title("Jetson Orin: Throughput & Target Success", fontsize=12, fontweight="bold", pad=10)
    ax2.set_ylim(0, max(throughputs) * 1.25)
    ax2.grid(axis="y", alpha=0.3)
    
    # Secondary axis for success rate
    ax2b = ax2.twinx()
    line = ax2b.plot(x, success_rates, color="#E24B4A", marker="o", markersize=7,
                     linewidth=2, linestyle="-", zorder=5, label="Target Success Rate (%)")
    ax2b.set_ylim(0, 130)
    ax2b.set_ylabel("Target Success Rate (%)", fontsize=12, fontweight="bold", color="#E24B4A")
    ax2b.tick_params(axis="y", colors="#E24B4A", labelsize=10)
    ax2b.yaxis.set_major_formatter(mticker.FormatStrFormatter("%g%%"))
    
    # Add value labels on bars
    for bar, val in zip(bars2, throughputs):
        ax2.text(bar.get_x() + bar.get_width() / 2, val + 0.1,
                f"{val:.2f}", ha="center", va="bottom", fontsize=10, fontweight="bold", color="#333")
    
    # Add success rate labels
    for xi, sr in zip(x, success_rates):
        ax2b.text(xi, sr + 4, f"{sr:.0f}%", ha="center", va="bottom", fontsize=9, fontweight="bold", color="#E24B4A")
    
    # Legend
    lines1, labels1 = ax2.get_legend_handles_labels()
    lines2, labels2 = ax2b.get_legend_handles_labels()
    ax2.legend(lines1 + lines2, ["Throughput (diag/s)"] + labels2, fontsize=10, frameon=False, loc="upper left")
    
    plt.subplots_adjust(wspace=0.35)
    output_file = output_dir / "08_jetson_orin_performance.png"
    plt.savefig(output_file, dpi=300, bbox_inches="tight")
    print(f"✅ Saved: {output_file}")
    plt.close()


if __name__ == "__main__":
    loader = BenchmarkLoader(Path("../../outputs"))
    plot_jetson_orin(loader, Path("./"))