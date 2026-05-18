import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
from pathlib import Path
from data_loader import BenchmarkLoader
from statistics import mean


PLATFORM_COLORS = {
    "desktop-legion": "#2196F3",   # azul
    "jetson-nano":    "#FF9800",   # laranja
    "jetson-orin":    "#4CAF50",   # verde
}

PLATFORM_LABELS = {
    "desktop-legion": "Desktop Legion",
    "jetson-nano":    "Jetson Nano",
    "jetson-orin":    "Jetson AGX Orin",
}


def plot_slm_vs_pdi(loader: BenchmarkLoader, output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)

    env_model_times: dict[tuple, dict] = {}
    for record in loader.data:
        key = (record["environment"], record["model"])
        env_model_times.setdefault(key, {"pdi": [], "slm": []})
        env_model_times[key]["pdi"].append(record["pdi_per_image_ms"])
        env_model_times[key]["slm"].append(record["slm_per_diagnosis_s"] * 1000)

    # Ordena para agrupar por plataforma
    sorted_keys = sorted(env_model_times.keys(), key=lambda k: (k[0], k[1]))

    labels, pdi_means, slm_means, colors = [], [], [], []
    for (env, model) in sorted_keys:
        times = env_model_times[(env, model)]
        labels.append(f"{model}")
        pdi_means.append(mean(times["pdi"]))
        slm_means.append(mean(times["slm"]))
        colors.append(PLATFORM_COLORS.get(env, "#999999"))

    x = np.arange(len(labels))
    width = 0.35

    fig, ax = plt.subplots(figsize=(15, 7))

    bars_pdi = ax.bar(
        x - width / 2, pdi_means, width,
        color=colors, alpha=0.55,
        hatch="///", edgecolor="white", linewidth=0.8,
        label="_nolegend_"
    )
    bars_slm = ax.bar(
        x + width / 2, slm_means, width,
        color=colors, alpha=0.92,
        edgecolor="white", linewidth=0.8,
        label="_nolegend_"
    )

    # Escala log — essencial para esta faixa de valores
    ax.set_yscale("log")
    ax.set_ylim(bottom=5)

    # Linha de referência: 1000ms = 1s (meta de latência)
    ax.axhline(1000, color="#E53935", linestyle="--", linewidth=1.4,
               label="Target (1.0 s)")

    # Rótulos de valor nas barras
    for bar in list(bars_pdi) + list(bars_slm):
        h = bar.get_height()
        label_text = f"{h:.0f}" if h >= 10 else f"{h:.1f}"
        ax.text(
            bar.get_x() + bar.get_width() / 2, h * 1.15,
            label_text,
            ha="center", va="bottom", fontsize=8, fontweight="bold"
        )

    # Linhas verticais separando plataformas
    platforms = [k[0] for k in sorted_keys]
    for i in range(1, len(platforms)):
        if platforms[i] != platforms[i - 1]:
            ax.axvline(i - 0.5, color="#CCCCCC", linestyle="-", linewidth=1.2)

    # Anotações de plataforma no topo do gráfico
    platform_groups: dict[str, list[int]] = {}
    for i, (env, _) in enumerate(sorted_keys):
        platform_groups.setdefault(env, []).append(i)

    ax_top = ax.secondary_xaxis("top")
    ax_top.set_xlim(ax.get_xlim())
    ax_top.set_xticks([np.mean(idxs) for idxs in platform_groups.values()])
    ax_top.set_xticklabels(
        [PLATFORM_LABELS.get(env, env) for env in platform_groups],
        fontsize=11, fontweight="bold"
    )
    ax_top.tick_params(length=0)

    # Eixos e títulos
    ax.set_ylabel("Time (ms) — log scale", fontsize=12, fontweight="bold")
    ax.set_title(
        "Comparison: PDI vs SLM Time by Environment/Model\n(which component is the bottleneck?)",
        fontsize=13, fontweight="bold", pad=28
    )
    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=10)
    ax.grid(axis="y", alpha=0.25, which="both")

    # Legenda: cores de plataforma + padrão de hachura
    platform_patches = [
        mpatches.Patch(color=c, label=PLATFORM_LABELS[env])
        for env, c in PLATFORM_COLORS.items()
    ]
    style_patches = [
        mpatches.Patch(facecolor="#999", hatch="///", edgecolor="white",
                       alpha=0.55, label="PDI (Computer Vision)"),
        mpatches.Patch(facecolor="#999", edgecolor="white",
                       alpha=0.92, label="SLM (Language Model)"),
    ]
    ax.legend(
        handles=platform_patches + [plt.Line2D([0], [0], color="#E53935",
                 linestyle="--", linewidth=1.4, label="Target (1.0 s)")] + style_patches,
        fontsize=10, loc="upper left", framealpha=0.9
    )

    plt.tight_layout()
    output_file = output_dir / "07_pdi_vs_slm.png"
    plt.savefig(output_file, dpi=300, bbox_inches="tight")
    print(f"✅ Saved: {output_file}")
    plt.close()


if __name__ == "__main__":
    loader = BenchmarkLoader(Path("../../outputs"))
    plot_slm_vs_pdi(loader, Path("./"))