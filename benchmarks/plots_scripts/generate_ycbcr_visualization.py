#!/usr/bin/env python3
"""
YCbCr Decomposition Visualization

Generates a figure showing the original RGB image and its luminance/chrominance
components. Saves both a combined figure and individual component images to
benchmarks/plots_output/.

Note:
    Conceptually, the figure illustrates the YCbCr color space. OpenCV names
    the conversion as YCrCb and returns channels in the order Y, Cr, Cb.

Usage:
    From benchmarks/plots_scripts/:
        poetry run python generate_ycbcr_visualization.py

    From project root:
        poetry run python benchmarks/plots_scripts/generate_ycbcr_visualization.py
"""

import sys
from pathlib import Path

import cv2
import matplotlib.pyplot as plt


# Resolve paths relative to the project root.
PROJECT_ROOT = Path(__file__).parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"
PLOTS_OUTPUT = PROJECT_ROOT / "benchmarks" / "plots_output"

# Image used for the decomposition example.
IMG_PATH = (
    DATA_DIR
    / "uploads"
    / "testes_lab_orin_16_04_2026"
    / "batch_20260416_200002_74ee64"
    / "frame_00.jpg"
)


def save_image_panel(output_path: Path, image, cmap=None) -> None:
    """Save a single image panel without axes or margins."""
    fig, ax = plt.subplots(figsize=(3, 4), dpi=150)

    ax.imshow(
        image,
        cmap=cmap,
        vmin=None if cmap is None else 0,
        vmax=None if cmap is None else 255,
    )

    ax.axis("off")
    plt.subplots_adjust(left=0, right=1, top=1, bottom=0)
    plt.savefig(output_path, dpi=150, bbox_inches="tight", pad_inches=0)
    plt.close(fig)


def main() -> None:
    """Generate combined and individual YCbCr/YCrCb visualization panels."""
    PLOTS_OUTPUT.mkdir(parents=True, exist_ok=True)

    if not IMG_PATH.exists():
        print(f"Image not found: {IMG_PATH}")
        sys.exit(1)

    print(f"Reading image: {IMG_PATH}")

    # Load image using OpenCV's default BGR format.
    img_bgr = cv2.imread(str(IMG_PATH))

    if img_bgr is None:
        print(f"Image could not be loaded: {IMG_PATH}")
        sys.exit(1)

    # Convert BGR to RGB for visualization.
    img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)

    # OpenCV uses YCrCb order: Y, Cr, Cb.
    img_ycrcb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2YCrCb)
    y_channel = img_ycrcb[:, :, 0]
    cr_channel = img_ycrcb[:, :, 1]
    cb_channel = img_ycrcb[:, :, 2]

    # ================================================================
    # 1. Generate combined figure
    # ================================================================
    print("\nGenerating combined YCbCr decomposition figure...")

    fig, axes = plt.subplots(1, 4, figsize=(13, 3.2), dpi=150)

    titles = [
        "(a) Original (RGB)",
        "(b) Y (Luminance)",
        "(c) Cr (Red-diff)",
        "(d) Cb (Blue-diff)",
    ]

    images = [img_rgb, y_channel, cr_channel, cb_channel]
    cmaps = [None, "gray", "gray", "gray"]

    for ax, title, image, cmap in zip(axes, titles, images, cmaps):
        ax.imshow(
            image,
            cmap=cmap,
            vmin=None if cmap is None else 0,
            vmax=None if cmap is None else 255,
        )
        ax.set_title(title, fontsize=10, fontweight="bold", pad=4)
        ax.axis("off")

    plt.subplots_adjust(wspace=0.01, left=0.02, right=0.98, top=0.92, bottom=0.02)

    combined_path = PLOTS_OUTPUT / "ycbcr_decomposition_example.png"
    plt.savefig(combined_path, dpi=150, bbox_inches="tight")
    plt.close(fig)

    print(f"Combined figure saved to: {combined_path}")

    # ================================================================
    # 2. Generate individual component images
    # ================================================================
    print("\nGenerating individual component images...")

    components = {
        "ycbcr_a_rgb.png": (img_rgb, None),
        "ycbcr_b_Y.png": (y_channel, "gray"),
        "ycbcr_c_Cr.png": (cr_channel, "gray"),
        "ycbcr_d_Cb.png": (cb_channel, "gray"),
    }

    for filename, (image, cmap) in components.items():
        output_path = PLOTS_OUTPUT / filename
        save_image_panel(output_path, image, cmap)
        print(f"  Saved {filename}")

    print(f"\nAll visualizations saved to: {PLOTS_OUTPUT}")


if __name__ == "__main__":
    main()