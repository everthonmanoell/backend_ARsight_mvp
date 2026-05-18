"""
ARSight visual theme for matplotlib
Import e chame apply_arsight_theme() antes de criar qualquer figura.
"""

import matplotlib.pyplot as plt
import matplotlib as mpl
from matplotlib import font_manager


# ── Paleta ────────────────────────────────────────────────────────────────────

BG_PRIMARY  = "#0D0E1A"
BG_CARD     = "#12142A"
BG_SURFACE  = "#1A1E35"
BORDER      = "#1E2235"

TEXT_PRIMARY   = "#E8EDF8"
TEXT_SECONDARY = "#C8D0E8"
TEXT_MUTED     = "#8899BB"

TEAL       = "#62CDAA"   # pass / ok / GPU
AMBER      = "#FAC775"   # qwen / warning
BLUE_VIO   = "#7B8CDE"   # PDI / Computer Vision
LIGHT_BLUE = "#A8C1F8"   # SLM / Language Model
CORAL      = "#F08060"   # fail / high risk
RED_LINE   = "#E05555"   # target lines (substituindo o vermelho padrão)
GREEN_LINE = "#62CDAA"   # target lines positivas

COLORS = {
    "qwen":      AMBER,
    "qwen-cpu":  "#E8A84A",   # amber mais escuro
    "qwen-gpu":  TEAL,
    "dialogpt":  LIGHT_BLUE,
    "phi":       BLUE_VIO,
    "pdi":       BLUE_VIO,
    "slm":       LIGHT_BLUE,
}


# ── rcParams ──────────────────────────────────────────────────────────────────

def apply_arsight_theme() -> None:
    """Aplica o tema ARSight globalmente no matplotlib."""
    mpl.rcParams.update({
        # Figura
        "figure.facecolor":      BG_PRIMARY,
        "figure.edgecolor":      BG_PRIMARY,
        "axes.facecolor":        BG_CARD,
        "axes.edgecolor":        BORDER,
        "axes.labelcolor":       TEXT_SECONDARY,
        "axes.titlecolor":       TEXT_PRIMARY,
        "axes.spines.top":       False,
        "axes.spines.right":     False,
        "axes.spines.left":      False,
        "axes.spines.bottom":    True,

        # Grid
        "axes.grid":             True,
        "grid.color":            BORDER,
        "grid.linewidth":        0.6,
        "grid.linestyle":        "--",
        "grid.alpha":            0.6,

        # Ticks
        "xtick.color":           TEXT_MUTED,
        "ytick.color":           TEXT_MUTED,
        "xtick.labelsize":       10,
        "ytick.labelsize":       10,
        "xtick.direction":       "out",
        "ytick.direction":       "out",

        # Texto
        "text.color":            TEXT_PRIMARY,
        "font.family":           "sans-serif",
        "font.sans-serif":       ["Inter", "SF Pro Display", "Segoe UI", "DejaVu Sans"],
        "font.size":             11,

        # Legenda
        "legend.facecolor":      BG_SURFACE,
        "legend.edgecolor":      BORDER,
        "legend.labelcolor":     TEXT_SECONDARY,
        "legend.fontsize":       10,
        "legend.framealpha":     0.95,

        # Salvamento
        "savefig.facecolor":     BG_PRIMARY,
        "savefig.edgecolor":     BG_PRIMARY,
    })


THEME_PAPER = {
    "figure.facecolor":   "white",
    "axes.facecolor":     "white",
    "axes.edgecolor":     "#CCCCCC",
    "axes.labelcolor":    "#222222",
    "axes.titlecolor":    "#111111",
    "axes.spines.top":    False,
    "axes.spines.right":  False,
    "axes.spines.left":   False,
    "grid.color":         "#E5E5E5",
    "grid.linewidth":     0.5,
    "text.color":         "#222222",
    "xtick.color":        "#555555",
    "ytick.color":        "#555555",
    "legend.facecolor":   "white",
    "legend.edgecolor":   "#CCCCCC",
    "legend.labelcolor":  "#222222",
    "savefig.facecolor":  "white",
    "font.sans-serif":    ["Helvetica Neue", "Arial", "DejaVu Sans"],
    "font.size":          10,
}

# Paleta paper: distinguível em P&B por valor (escuro/médio/claro)
# + hachuras para garantir distinção ao imprimir
PAPER_PDI_COLOR  = "#2C3E6B"   # azul escuro
PAPER_SLM_COLOR  = "#8BAED4"   # azul claro
PAPER_BOTTLENECK = "#E8A030"   # âmbar — ainda funciona em P&B por ser mais claro

PAPER_PDI_HATCH  = ""          # sólido
PAPER_SLM_HATCH  = "//"        # hachura diagonal
PAPER_BOTT_HATCH = "xx"        # hachura cruzada

def apply_paper_theme() -> None:
    """Tema para publicação ACM/IEEE — fundo branco, legível em P&B."""
    import matplotlib as mpl
    mpl.rcParams.update(THEME_PAPER)