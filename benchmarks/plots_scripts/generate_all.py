"""
Generate All Benchmark Plots

Coordinator script that runs all individual plot scripts and generates an HTML
report with the resulting figures.

Usage:
    poetry run python benchmarks/plots_scripts/generate_all.py
"""

import sys
import traceback
from pathlib import Path
from typing import Callable, Dict, List, Tuple

# Allow importing local plotting utilities when running from the project root.
SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from data_loader import BenchmarkLoader
from plot_01_env_performance import plot_env_performance
from plot_02_model_comparison import plot_model_comparison
from plot_03_accuracy_by_batch import plot_accuracy_by_batch
from plot_04_latency_distribution import plot_latency_distribution
from plot_05_cross_env_speedup import plot_cross_env_comparison
from plot_06_pdi_vs_slm import plot_slm_vs_pdi
from plot_07_jetson_nano_performance import plot_jetson_nano
from plot_08_jetson_orin_performance import plot_jetson_orin
from plot_09_desktop_legion_performance import plot_desktop_legion
from plot_10_qwen_cpu_vs_gpu_nano import plot_qwen_cpu_vs_gpu


def generate_all_plots(
    outputs_base: Path = None,
    plots_output_dir: Path = None,
) -> None:
    """Run all benchmark plot generators and create the HTML report."""
    if outputs_base is None:
        outputs_base = SCRIPT_DIR.parent.parent / "outputs"

    if plots_output_dir is None:
        plots_output_dir = SCRIPT_DIR.parent / "plots_output"

    print("=" * 80)
    print("GENERATING ALL BENCHMARK CHARTS")
    print("=" * 80)

    plots_output_dir.mkdir(parents=True, exist_ok=True)

    print("\nLoading data from JSON files...")
    loader = BenchmarkLoader(outputs_base)
    stats = loader.stats()

    print(f"  Total runs: {stats.get('total_runs', 0)}")
    print(f"  Environments: {stats.get('environments', [])}")
    print(f"  Models: {stats.get('models', [])}")
    print(f"  Batches: {stats.get('batches', [])}")

    print("\n" + "=" * 80)
    print("GENERATING PLOTS")
    print("=" * 80)

    plots: List[Tuple[str, Callable[[BenchmarkLoader, Path], None]]] = [
        ("Performance by Environment - Latency and Throughput", plot_env_performance),
        ("Model Comparison - Latency and Accuracy", plot_model_comparison),
        ("Accuracy by Batch", plot_accuracy_by_batch),
        ("Latency Distribution", plot_latency_distribution),
        ("Cross-Environment Speedup", plot_cross_env_comparison),
        ("PDI vs SLM", plot_slm_vs_pdi),
        ("Jetson Nano Performance", plot_jetson_nano),
        ("Jetson AGX Orin Performance", plot_jetson_orin),
        ("Desktop Legion Performance", plot_desktop_legion),
        ("Qwen CPU vs GPU on Jetson Nano", plot_qwen_cpu_vs_gpu),
    ]

    failed_plots = []

    for idx, (description, plot_func) in enumerate(plots, 1):
        print(f"\n[{idx}/{len(plots)}] {description}...")

        try:
            plot_func(loader, plots_output_dir)
        except Exception as exc:
            failed_plots.append(description)
            print(f"  ERROR: {exc}")
            traceback.print_exc()

    print("\n" + "=" * 80)
    print("GENERATING HTML REPORT")
    print("=" * 80)

    generate_html_report(loader, plots_output_dir, stats)

    print("\n" + "=" * 80)

    if failed_plots:
        print("PLOTS GENERATED WITH WARNINGS")
        print("=" * 80)
        print("The following plots failed:")
        for plot_name in failed_plots:
            print(f"  - {plot_name}")
    else:
        print("ALL CHARTS GENERATED SUCCESSFULLY")
        print("=" * 80)

    print(f"\nCharts saved in: {plots_output_dir.resolve()}")
    print("Summary statistics:")
    print(f"  - Average SLM latency: {stats.get('avg_slm_per_diag', 0):.3f}s")
    print(f"  - Average accuracy: {stats.get('avg_accuracy', 0):.1f}%")
    print(f"  - Target achievement rate: {stats.get('target_met_rate', 0) * 100:.1f}%")


def generate_html_report(
    loader: BenchmarkLoader,
    plots_dir: Path,
    stats: Dict,
) -> None:
    """Generate an HTML report with all benchmark charts."""

    plot_descriptions = {
        "01_env_latency.png": "Environment Performance - SLM latency across Nano, Orin, and Legion",
        "01_env_throughput.png": "Environment Performance - Throughput across environments",
        "02_model_latency.png": "Model Comparison - SLM latency for DialoGPT, Qwen, and Phi by environment",
        "02_model_accuracy.png": "Model Comparison - Accuracy for each model across environments",
        "03_accuracy_by_batch.png": "Accuracy by Batch - Consistency across test batches",
        "04_latency_distribution.png": "Latency Distribution - Variability and outliers across environments",
        "05_cross_env_speedup.png": "Cross-Environment Speedup - Relative performance against Desktop Legion baseline",
        "06_pdi_vs_slm.png": "PDI vs SLM Analysis - Bottleneck comparison between vision and language components",
        "07_jetson_nano_latency.png": "Jetson Nano - SLM latency by model",
        "07_jetson_nano_throughput.png": "Jetson Nano - Throughput by model",
        "07_jetson_nano_success.png": "Jetson Nano - Target success rate by model",
        "08_jetson_orin_latency.png": "Jetson AGX Orin - SLM latency by model",
        "08_jetson_orin_throughput.png": "Jetson AGX Orin - Throughput by model",
        "08_jetson_orin_success.png": "Jetson AGX Orin - Target success rate by model",
        "09_desktop_legion_latency.png": "Desktop Legion - SLM latency by model",
        "09_desktop_legion_throughput.png": "Desktop Legion - Throughput by model",
        "09_desktop_legion_success.png": "Desktop Legion - Target success rate by model",
        "10_qwen_nano_latency_cpu_vs_gpu.png": "Qwen on Jetson Nano - CPU vs GPU latency comparison",
        "10_qwen_nano_throughput_cpu_vs_gpu.png": "Qwen on Jetson Nano - CPU vs GPU throughput comparison",
        "10_qwen_nano_success_cpu_vs_gpu.png": "Qwen on Jetson Nano - CPU vs GPU target success rate",
    }

    def render_plot(img_name: str) -> str:
        """Render one image block if the image exists."""
        img_path = plots_dir / img_name

        if not img_path.exists():
            return ""

        description = plot_descriptions.get(img_name, img_name)

        return f"""
        <div class="plot-container">
            <h4>{description}</h4>
            <img src="{img_name}" alt="{img_name}">
        </div>
"""

    def render_section(title: str, image_names: List[str], subtitle: str = None) -> str:
        """Render a complete report section."""
        subtitle_html = f"<h3>{subtitle}</h3>" if subtitle else ""
        plots_html = "".join(render_plot(img_name) for img_name in image_names)

        return f"""
    <div class="section">
        <h2>{title}</h2>
        {subtitle_html}
        {plots_html}
    </div>
"""

    html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Benchmark Report - AR Diagnostic MVP</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        h1, h2 {{
            color: #333;
            border-bottom: 3px solid #007acc;
            padding-bottom: 10px;
        }}
        h3 {{
            color: #444;
            border-bottom: 1px solid #ddd;
            padding-bottom: 5px;
            margin-top: 25px;
        }}
        .summary {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            margin: 20px 0;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .stat-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin: 15px 0;
        }}
        .stat-box {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 15px;
            border-radius: 8px;
            text-align: center;
        }}
        .stat-box h3 {{
            margin: 0;
            font-size: 14px;
            opacity: 0.9;
            border: none;
            padding: 0;
        }}
        .stat-box .value {{
            font-size: 28px;
            font-weight: bold;
            margin-top: 10px;
        }}
        .section {{
            background: white;
            padding: 20px;
            margin: 20px 0;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .section h2 {{
            margin-top: 0;
        }}
        .plot-container {{
            background: white;
            padding: 20px;
            margin: 15px 0;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .plot-container img {{
            max-width: 100%;
            height: auto;
            border-radius: 4px;
        }}
        .plot-container h4 {{
            margin-top: 0;
            font-size: 13px;
            color: #666;
        }}
        footer {{
            text-align: center;
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #ddd;
            color: #666;
            font-size: 12px;
        }}
    </style>
</head>
<body>
    <h1>Benchmark Report - AR Diagnostic MVP</h1>

    <div class="summary">
        <h2>Executive Summary</h2>
        <div class="stat-grid">
            <div class="stat-box">
                <h3>Total Runs</h3>
                <div class="value">{stats.get('total_runs', 0)}</div>
            </div>
            <div class="stat-box">
                <h3>Environments</h3>
                <div class="value">{len(stats.get('environments', []))}</div>
            </div>
            <div class="stat-box">
                <h3>Models Tested</h3>
                <div class="value">{len(stats.get('models', []))}</div>
            </div>
            <div class="stat-box">
                <h3>Batches</h3>
                <div class="value">{len(stats.get('batches', []))}</div>
            </div>
            <div class="stat-box">
                <h3>Average SLM Latency</h3>
                <div class="value">{stats.get('avg_slm_per_diag', 0):.3f}s</div>
            </div>
            <div class="stat-box">
                <h3>Average Accuracy</h3>
                <div class="value">{stats.get('avg_accuracy', 0):.1f}%</div>
            </div>
            <div class="stat-box">
                <h3>Target Met Rate</h3>
                <div class="value">{stats.get('target_met_rate', 0) * 100:.1f}%</div>
            </div>
        </div>
    </div>

    <div class="summary">
        <h2>General Information</h2>
        <ul>
            <li><strong>Environments:</strong> {', '.join(sorted(stats.get('environments', [])))}</li>
            <li><strong>Models:</strong> {', '.join(sorted(stats.get('models', [])))}</li>
            <li><strong>Batches:</strong> {', '.join(sorted(stats.get('batches', [])))}</li>
        </ul>
    </div>
"""

    html_content += render_section(
        "Environment Performance",
        ["01_env_latency.png", "01_env_throughput.png"],
    )

    html_content += render_section(
        "Model Comparison",
        ["02_model_latency.png", "02_model_accuracy.png"],
    )

    html_content += render_section(
        "Consistency and Distribution",
        ["03_accuracy_by_batch.png", "04_latency_distribution.png"],
    )

    html_content += render_section(
        "Cross-Environment and Component Analysis",
        ["05_cross_env_speedup.png", "06_pdi_vs_slm.png"],
    )

    html_content += """
    <div class="section">
        <h2>Per-Environment Performance Analysis</h2>

        <h3>Jetson Nano</h3>
"""

    for img_name in [
        "07_jetson_nano_latency.png",
        "07_jetson_nano_throughput.png",
        "07_jetson_nano_success.png",
    ]:
        html_content += render_plot(img_name)

    html_content += """
        <h3>Jetson AGX Orin</h3>
"""

    for img_name in [
        "08_jetson_orin_latency.png",
        "08_jetson_orin_throughput.png",
        "08_jetson_orin_success.png",
    ]:
        html_content += render_plot(img_name)

    html_content += """
        <h3>Desktop Legion</h3>
"""

    for img_name in [
        "09_desktop_legion_latency.png",
        "09_desktop_legion_throughput.png",
        "09_desktop_legion_success.png",
    ]:
        html_content += render_plot(img_name)

    html_content += """
    </div>
"""

    html_content += render_section(
        "Special Analysis: Qwen CPU vs GPU on Jetson Nano",
        [
            "10_qwen_nano_latency_cpu_vs_gpu.png",
            "10_qwen_nano_throughput_cpu_vs_gpu.png",
            "10_qwen_nano_success_cpu_vs_gpu.png",
        ],
    )

    html_content += """
    <footer>
        <p>Automatically generated by the benchmark analysis script.</p>
        <p>High-resolution charts (300 DPI) ready for inclusion in documents and presentations.</p>
        <p>Note: each plot focuses on a single metric for clarity and flexibility in final thesis figure selection.</p>
    </footer>
</body>
</html>
"""

    report_file = plots_dir / "index.html"

    with open(report_file, "w", encoding="utf-8") as file:
        file.write(html_content)

    print(f"HTML report saved to: {report_file}")


if __name__ == "__main__":
    generate_all_plots()