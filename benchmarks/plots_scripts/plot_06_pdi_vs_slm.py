"""
Plot 6: PDI vs SLM Comparison
Shows which component (PDI computer vision vs SLM language model) is the bottleneck
"""

import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
from data_loader import BenchmarkLoader
from statistics import mean


def plot_slm_vs_pdi(loader: BenchmarkLoader, output_dir: Path) -> None:
    """Creates chart comparing PDI vs SLM time"""
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    summary = loader.summary_by_env_model()
    
    # Agrupa por (environment, model)
    env_model_times = {}
    
    for record in loader.data:
        key = (record["environment"], record["model"])
        if key not in env_model_times:
            env_model_times[key] = {"pdi": [], "slm": []}
        
        env_model_times[key]["pdi"].append(record["pdi_per_image_ms"])
        env_model_times[key]["slm"].append(record["slm_per_diagnosis_s"] * 1000)  # converte para ms
    
    # Prepare data for plot
    labels = []
    pdi_means = []
    slm_means = []
    
    for (env, model), times in sorted(env_model_times.items()):
        labels.append(f"{env}\n{model}")
        pdi_means.append(mean(times["pdi"]))
        slm_means.append(mean(times["slm"]))
    
    x = np.arange(len(labels))
    width = 0.35
    
    fig, ax = plt.subplots(figsize=(14, 6))
    
    bars1 = ax.bar(x - width/2, pdi_means, width, label="PDI (Computer Vision)", 
                   color="#1F1F1F", alpha=0.75, edgecolor="#000", linewidth=1.2)
    bars2 = ax.bar(x + width/2, slm_means, width, label="SLM (Language Model)", 
                   color="#737373", alpha=0.75, edgecolor="#000", linewidth=1.2)
    
    ax.set_ylabel("Time (ms)", fontsize=12, fontweight="bold")
    ax.set_title("Comparison: PDI vs SLM Time by Environment/Model\n(which component is the bottleneck?)", 
                fontsize=13, fontweight="bold")
    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=10)
    ax.legend(fontsize=11)
    ax.grid(axis="y", alpha=0.3)
    
    # Adicionar valores nas barras
    for bars in [bars1, bars2]:
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'{height:.1f}', ha='center', va='bottom', fontsize=9, fontweight="bold")
    
    plt.tight_layout()
    output_file = output_dir / "06_pdi_vs_slm.png"
    plt.savefig(output_file, dpi=300, bbox_inches="tight")
    print(f"✅ Saved: {output_file}")
    plt.close()


if __name__ == "__main__":
    loader = BenchmarkLoader(Path("../../outputs"))
    plot_slm_vs_pdi(loader, Path("./"))
