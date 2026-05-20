"""
ARSight visual theme for matplotlib.
"""

import matplotlib as mpl

# ----------------------------------------------------------------------------------------------------------------
# Color palette 
# ----------------------------------------------------------------------------------------------------------------
BG_PRIMARY = "#0D0E1A"
BG_CARD = "#12142A"
BG_SURFACE = "#1A1E35"
BORDER = "#1E2235"

TEXT_PRIMARY = "#E8EDF8"
TEXT_SECONDARY = "#C8D0E8"
TEXT_MUTED = "#8899BB"

TEAL = "#62CDAA"        # pass / ok / GPU
AMBER = "#FAC775"       # Qwen / warning
BLUE_VIO = "#7B8CDE"    # PDI / Computer Vision
LIGHT_BLUE = "#A8C1F8"  # SLM / Language Model
CORAL = "#F08060"       # fail / high risk
RED_LINE = "#E05555"    # negative target lines
GREEN_LINE = "#62CDAA"  # positive target lines

COLORS = {
    "qwen": AMBER,
    "qwen-cpu": "#E8A84A",
    "qwen-gpu": TEAL,
    "dialogpt": LIGHT_BLUE,
    "phi": BLUE_VIO,
    "pdi": BLUE_VIO,
    "slm": LIGHT_BLUE,
}

# ----------------------------------------------------------------------------------------------------------------
# ARSight dark theme 
# ----------------------------------------------------------------------------------------------------------------
def apply_arsight_theme() -> None:
    """Apply the ARSight dark theme globally to matplotlib."""
    mpl.rcParams.update(
        {
            # Figure and axes.
            "figure.facecolor": BG_PRIMARY,
            "figure.edgecolor": BG_PRIMARY,
            "axes.facecolor": BG_CARD,
            "axes.edgecolor": BORDER,
            "axes.labelcolor": TEXT_SECONDARY,
            "axes.titlecolor": TEXT_PRIMARY,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.spines.left": False,
            "axes.spines.bottom": True,

            # Grid.
            "axes.grid": True,
            "grid.color": BORDER,
            "grid.linewidth": 0.6,
            "grid.linestyle": "--",
            "grid.alpha": 0.6,

            # Ticks.
            "xtick.color": TEXT_MUTED,
            "ytick.color": TEXT_MUTED,
            "xtick.labelsize": 10,
            "ytick.labelsize": 10,
            "xtick.direction": "out",
            "ytick.direction": "out",

            # Text.
            "text.color": TEXT_PRIMARY,
            "font.family": "sans-serif",
            "font.sans-serif": [
                "Inter",
                "SF Pro Display",
                "Segoe UI",
                "DejaVu Sans",
            ],
            "font.size": 11,

            # Legend.
            "legend.facecolor": BG_SURFACE,
            "legend.edgecolor": BORDER,
            "legend.labelcolor": TEXT_SECONDARY,
            "legend.fontsize": 10,
            "legend.framealpha": 0.95,

            # Savefig.
            "savefig.facecolor": BG_PRIMARY,
            "savefig.edgecolor": BG_PRIMARY,
        }
    )


# ----------------------------------------------------------------------------------------------------------------
# Publication theme
# ----------------------------------------------------------------------------------------------------------------

THEME_PAPER = {
    "figure.facecolor": "white",
    "axes.facecolor": "white",
    "axes.edgecolor": "#CCCCCC",
    "axes.labelcolor": "#222222",
    "axes.titlecolor": "#111111",
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.spines.left": False,
    "grid.color": "#E5E5E5",
    "grid.linewidth": 0.5,
    "text.color": "#222222",
    "xtick.color": "#555555",
    "ytick.color": "#555555",
    "legend.facecolor": "white",
    "legend.edgecolor": "#CCCCCC",
    "legend.labelcolor": "#222222",
    "savefig.facecolor": "white",
    "font.sans-serif": ["Helvetica Neue", "Arial", "DejaVu Sans"],
    "font.size": 10,
}

# ----------------------------------------------------------------------------------------------------------------
# Paper palette.
# Colors are distinguishable by luminance and supported by hatch patterns for grayscale printing.
# ----------------------------------------------------------------------------------------------------------------
PAPER_PDI_COLOR = "#2C3E6B"       # Dark blue.
PAPER_SLM_COLOR = "#8BAED4"       # Light blue.
PAPER_BOTTLENECK = "#E8A030"      # Amber, still distinguishable in grayscale.

PAPER_PDI_HATCH = ""              # Solid.
PAPER_SLM_HATCH = "//"            # Diagonal hatch.
PAPER_BOTT_HATCH = "xx"           # Cross hatch.


def apply_paper_theme() -> None:
    """Apply a publication-ready theme for ACM/IEEE-style plots."""
    mpl.rcParams.update(THEME_PAPER)


def apply_theme(mode: str = "arsight") -> None:
    """
    Apply one of the available matplotlib themes.

    Args:
        mode: Theme name. Use "arsight" for the dark project theme or "paper"
            for the publication-ready white theme.

    Raises:
        ValueError: If an unknown theme mode is provided.
    """
    if mode == "arsight":
        apply_arsight_theme()
    elif mode == "paper":
        apply_paper_theme()
    else:
        raise ValueError(f"Unknown theme mode: {mode}. Use 'arsight' or 'paper'.")