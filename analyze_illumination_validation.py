#!/usr/bin/env python3
"""
Illumination Analysis Validation
Generates scatter plot with real distribution of scores and classifications
use: poetry run python analyze_illumination_validation.py
"""
import os
import glob
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from PIL import Image
import yaml
from app.pdi.illumination import IlluminationAnalyzer

# Configuração
DATA_ILLUMINATION = "data/illumination"
DATA_UPLOADS = "data/uploads"
OUTPUT_PLOT = "docs/validation_illumination_scatter.png"

# Colors for each classification
COLORS = {
    "overexposed": "#FF6B6B",     # Red
    "underexposed": "#1A1A2E",    # Dark blue
    "adequate": "#51CF66",        # Green
    "acceptable": "#FFD93D",      # Yellow
    "poor": "#A23B72",            # Purple
}

LABELS_EN = {
    "overexposed": "Overexposed",
    "underexposed": "Underexposed",
    "adequate": "Adequate",
    "acceptable": "Acceptable",
    "poor": "Poor",
}


def load_config():
    """Loads threshold configuration"""
    config_path = "app/config/thresholds.yaml"
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)


def process_images(data_dirs):
    """
    Processes all images in directories
    Returns: list of (score, classification, path)
    """
    analyzer = IlluminationAnalyzer(config=load_config())
    results = []
    
    for data_dir in data_dirs:
        image_files = glob.glob(f"{data_dir}/**/*.jpg", recursive=True)
        image_files += glob.glob(f"{data_dir}/**/*.jpeg", recursive=True)
        image_files += glob.glob(f"{data_dir}/**/*.png", recursive=True)
        
        print(f"\n📁 Processing {data_dir} ({len(image_files)} images)...")
        
        for img_path in image_files:
            try:
                img = Image.open(img_path).convert("RGB")
                score, details = analyzer.analyze(img)
                label = details.get("label", "unknown")
                
                results.append({
                    "score": score,
                    "label": label,
                    "path": img_path,
                    "mean_luma": details.get("mean_luma", 0),
                    "std_luma": details.get("std_luma", 0),
                    "uniformity": details.get("uniformity", 0),
                })
                
                if len(results) % 50 == 0:
                    print(f"  ✓ {len(results)} images processed...")
                    
            except Exception as e:
                print(f"  ⚠️  Error in {img_path}: {e}")
    
    return results


def create_scatter_plot(results):
    """Creates scatter plot with score distribution (optimized for ACM paper format)"""
    from collections import Counter
    from matplotlib.patches import Patch

    scores = [r["score"] for r in results]
    labels = [r["label"] for r in results]

    # Remove Poor do eixo Y pois não há pontos — compacta o plot
    label_to_y = {
        "overexposed":  4,
        "adequate":     3,
        "acceptable":   2,
        "underexposed": 1,
    }

    y_positions = [label_to_y.get(l, 0) for l in labels]
    colors = [COLORS.get(l, "#888888") for l in labels]
    distribution = Counter(labels)

    # Print distribution
    print("\n📊 Distribution of classifications:")
    for label, count in sorted(distribution.items()):
        pct = 100 * count / len(results)
        print(f"  {LABELS_EN.get(label, label)}: {count} ({pct:.1f}%)")

    # Figura menor para caber no paper ACM (12x5 em vez de 14x8)
    fig, ax = plt.subplots(figsize=(12, 5), dpi=150)

    np.random.seed(42)
    y_jitter = np.array(y_positions) + np.random.normal(0, 0.12, len(y_positions))

    ax.scatter(scores, y_jitter, c=colors, s=60, alpha=0.6,
               edgecolors="black", linewidth=0.4)

    # Linhas de threshold — labels no topo ficam livres agora
    for x in [0.50, 0.70]:
        ax.axvline(x=x, color="#666666", linestyle="--", linewidth=1.5, alpha=0.7)
        ax.text(x, 4.55, f"S = {x}", ha="center", fontsize=9,
                bbox=dict(boxstyle="round,pad=0.2", facecolor="white", alpha=0.9))

    ax.set_xlabel("Illumination Score (S)", fontsize=12, fontweight="bold")
    ax.set_ylabel("Classification", fontsize=12, fontweight="bold")
    ax.set_xlim(-0.05, 1.05)
    ax.set_ylim(0.5, 5.0)

    ax.set_yticks([1, 2, 3, 4])
    ax.set_yticklabels(["Underexposed", "Acceptable", "Adequate", "Overexposed"])

    ax.grid(axis="x", alpha=0.3, linestyle=":")

    # Legenda embaixo do plot — fora da área de dados
    legend_elements = [
        Patch(facecolor=COLORS[k], edgecolor="black",
              label=f"{LABELS_EN[k]} (n={distribution.get(k, 0)})")
        for k in ["overexposed", "adequate", "acceptable", "underexposed"]
        if distribution.get(k, 0) > 0
    ]
    ax.legend(handles=legend_elements, loc="lower center",
              bbox_to_anchor=(0.5, -0.28), ncol=4,
              fontsize=10, framealpha=0.95)

    # Estatísticas no canto superior direito — região vazia
    stats_text = (
        f"n=320  |  Mean: {np.mean(scores):.2f}  |  "
        f"Median: {np.median(scores):.2f}  |  "
        f"Std: {np.std(scores):.2f}  |  "
        f"Range: [{np.min(scores):.2f}, {np.max(scores):.2f}]"
    )
    ax.text(0.98, 0.97, stats_text, transform=ax.transAxes,
            fontsize=8.5, verticalalignment="top", horizontalalignment="right",
            bbox=dict(boxstyle="round", facecolor="white", alpha=0.85))

    # Sem título — a caption do LaTeX cumpre esse papel no ACM
    plt.tight_layout()
    plt.subplots_adjust(bottom=0.22)
    plt.savefig(OUTPUT_PLOT, dpi=150, bbox_inches="tight")
    print(f"\n✅ Plot saved to: {OUTPUT_PLOT}")
    plt.close()


def generate_stats_table(results):
    """Generates statistics table by class"""
    from collections import defaultdict
    
    stats_by_class = defaultdict(lambda: {"scores": [], "lumas": [], "std": []})
    
    for r in results:
        label = r["label"]
        stats_by_class[label]["scores"].append(r["score"])
        stats_by_class[label]["lumas"].append(r["mean_luma"])
        stats_by_class[label]["std"].append(r["std_luma"])
    
    print("\n📈 Statistics Table by Class:")
    print("-" * 100)
    print(f"{'Class':<20} {'N':<8} {'Score (μ)':<15} {'Score (σ)':<15} {'μ_Y (μ)':<15} {'σ_Y (μ)':<15}")
    print("-" * 100)
    
    for label in ["overexposed", "underexposed", "adequate", "acceptable", "poor"]:
        if label in stats_by_class:
            data = stats_by_class[label]
            n = len(data["scores"])
            score_mean = np.mean(data["scores"])
            score_std = np.std(data["scores"])
            luma_mean = np.mean(data["lumas"])
            std_luma_mean = np.mean(data["std"])
            
            print(f"{LABELS_EN[label]:<20} {n:<8} {score_mean:<15.3f} {score_std:<15.3f} {luma_mean:<15.1f} {std_luma_mean:<15.1f}")
    
    print("-" * 100)


if __name__ == "__main__":
    print("🔍 Illumination Classification Validation")
    print("=" * 60)
    
    # Process images
    results = process_images([DATA_ILLUMINATION, DATA_UPLOADS])
    
    print(f"\n✅ Total images processed: {len(results)}")
    
    # Generate plot
    create_scatter_plot(results)
    
    # Generate statistics
    generate_stats_table(results)
    
    print("\n✨ Analysis complete!")
