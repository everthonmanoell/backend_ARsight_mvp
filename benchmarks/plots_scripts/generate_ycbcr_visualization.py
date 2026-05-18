#!/usr/bin/env python3
"""
YCbCr Decomposition Visualization

Generates a figure showing the original RGB image and its YCbCr components.
Saves both a combined figure and individual component images to benchmarks/plots_output/.

Usage:
  from benchmarks/plots_scripts/:
    poetry run python generate_ycbcr_visualization.py
  
  or from project root:
    poetry run python benchmarks/plots_scripts/generate_ycbcr_visualization.py
"""
import cv2
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
import sys

# Resolve paths relative to project root
PROJECT_ROOT = Path(__file__).parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"
PLOTS_OUTPUT = PROJECT_ROOT / "benchmarks" / "plots_output"
PLOTS_OUTPUT.mkdir(parents=True, exist_ok=True)

# Image to analyze
IMG_PATH = DATA_DIR / "uploads" / "testes_lab_orin_16_04_2026" / "batch_20260416_200002_74ee64" / "frame_00.jpg"

# Check if image exists
if not IMG_PATH.exists():
    print(f"❌ Image not found: {IMG_PATH}")
    sys.exit(1)

print(f"📁 Reading image: {IMG_PATH}")

# Load and convert image
img_bgr = cv2.imread(str(IMG_PATH))
img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
img_ycbcr = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2YCrCb)
Y, Cr, Cb = img_ycbcr[:,:,0], img_ycbcr[:,:,1], img_ycbcr[:,:,2]

# ================================
# 1. Generate combined figure
# ================================
print("\n📊 Generating combined YCbCr decomposition figure...")

fig, axes = plt.subplots(1, 4, figsize=(13, 3.2), dpi=150)

titles = ["(a) Original (RGB)", "(b) Y (Luminance)", "(c) Cr (Red-diff)", "(d) Cb (Blue-diff)"]
images = [img_rgb, Y, Cr, Cb]
cmaps  = [None, "gray", "gray", "gray"]

for ax, title, im, cmap in zip(axes, titles, images, cmaps):
    ax.imshow(im, cmap=cmap, vmin=(None if cmap is None else 0),
              vmax=(None if cmap is None else 255))
    ax.set_title(title, fontsize=10, fontweight="bold", pad=4)
    ax.axis("off")

plt.subplots_adjust(wspace=0.01, left=0.02, right=0.98, top=0.92, bottom=0.02)

combined_path = PLOTS_OUTPUT / "ycbcr_decomposition_example.png"
plt.savefig(combined_path, dpi=150, bbox_inches="tight")
plt.close()
print(f"✅ Combined figure: {combined_path}")

# ================================
# 2. Generate individual component images (optional)
# ================================
print("\n🖼️  Generating individual component images...")

components = {
    "ycbcr_a_rgb.png": (img_rgb, None),
    "ycbcr_b_Y.png":   (Y, "gray"),
    "ycbcr_c_Cr.png":  (Cr, "gray"),
    "ycbcr_d_Cb.png":  (Cb, "gray"),
}

for filename, (im, cmap) in components.items():
    fig, ax = plt.subplots(figsize=(3, 4), dpi=150)
    ax.imshow(im, cmap=cmap, vmin=(None if cmap is None else 0),
              vmax=(None if cmap is None else 255))
    ax.axis("off")
    plt.subplots_adjust(left=0, right=1, top=1, bottom=0)
    
    output_path = PLOTS_OUTPUT / filename
    plt.savefig(output_path, dpi=150, bbox_inches="tight", pad_inches=0)
    plt.close()
    print(f"  ✓ {filename}")

print(f"\n✨ All visualizations saved to: {PLOTS_OUTPUT}")
