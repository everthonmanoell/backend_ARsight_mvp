#!/usr/bin/env python3
"""
YCbCr Decomposition Visualization
Generates a figure showing the original RGB image and its YCbCr components.
use: poetry run python generate_ycbcr_visualization.py
"""
import cv2
import matplotlib.pyplot as plt

IMG_PATH = "data/uploads/testes_lab_orin_16_04_2026/batch_20260416_200002_74ee64/frame_00.jpg"
OUT_DIR = "images/plots/"

img_bgr = cv2.imread(IMG_PATH)
img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
img_ycbcr = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2YCrCb)
Y, Cr, Cb = img_ycbcr[:,:,0], img_ycbcr[:,:,1], img_ycbcr[:,:,2]

panels = [
    ("ycbcr_a_rgb.png", img_rgb, None),
    ("ycbcr_b_Y.png",   Y,       "gray"),
    ("ycbcr_c_Cr.png",  Cr,      "gray"),
    ("ycbcr_d_Cb.png",  Cb,      "gray"),
]

for filename, im, cmap in panels:
    fig, ax = plt.subplots(figsize=(3, 4), dpi=150)
    ax.imshow(im, cmap=cmap, vmin=(None if cmap is None else 0),
              vmax=(None if cmap is None else 255))
    ax.axis("off")
    plt.subplots_adjust(left=0, right=1, top=1, bottom=0)
    plt.savefig(OUT_DIR + filename, dpi=150, bbox_inches="tight", pad_inches=0)
    plt.close()
    print(f"✅ {filename}")