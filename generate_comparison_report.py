#!/usr/bin/env python3
"""
Gera relatório de comparação em HTML mostrando performance dos 3 ambientes
"""
import json
import csv
from pathlib import Path
from datetime import datetime
from typing import Any


def read_csv(filepath: Path) -> list[dict[str, Any]]:
    """Lê arquivo CSV"""
    if not filepath.exists():
        return []
    rows = []
    with filepath.open('r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
    return rows


def generate_html_report(out_dir: Path) -> None:
    """Gera relatório HTML com os dados do CSV"""
    summary_file = out_dir / "summary_by_env_model_batch.csv"
    speedup_file = out_dir / "speedup_vs_desktop_legion.csv"
    
    summary_rows = read_csv(summary_file)
    speedup_rows = read_csv(speedup_file)
    
    html_parts = []
    html_parts.append("""<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Relatório de Benchmark - 3 Ambientes</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .container {
            max-width: 1400px;
            margin: 0 auto;
            background-color: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        h1, h2 {
            color: #333;
            border-bottom: 3px solid #0066cc;
            padding-bottom: 10px;
        }
        h2 {
            margin-top: 40px;
            border-bottom-width: 2px;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
            font-size: 14px;
        }
        th {
            background-color: #0066cc;
            color: white;
            padding: 12px;
            text-align: left;
            font-weight: 600;
        }
        td {
            padding: 10px 12px;
            border-bottom: 1px solid #ddd;
        }
        tr:hover {
            background-color: #f9f9f9;
        }
        tr:nth-child(even) {
            background-color: #f5f5f5;
        }
        .env-desktop {
            background-color: #e3f2fd;
            font-weight: 600;
        }
        .env-nano {
            background-color: #fff3e0;
            font-weight: 600;
        }
        .env-orin {
            background-color: #e8f5e9;
            font-weight: 600;
        }
        .metric-good {
            color: #2e7d32;
            font-weight: 600;
        }
        .metric-warning {
            color: #f57c00;
            font-weight: 600;
        }
        .metric-bad {
            color: #c62828;
            font-weight: 600;
        }
        .timestamp {
            color: #666;
            font-size: 12px;
            margin-top: 20px;
        }
        .image-section {
            margin: 30px 0;
            text-align: center;
        }
        .image-section img {
            max-width: 100%;
            height: auto;
            border: 1px solid #ddd;
            border-radius: 4px;
            margin: 10px 0;
        }
        .summary-box {
            background-color: #f0f4f8;
            padding: 15px;
            border-radius: 4px;
            margin: 15px 0;
            border-left: 4px solid #0066cc;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Relatório de Benchmark - Performance 3 Ambientes</h1>
        <p>Estado da performance entre Desktop Legion, Jetson Nano e Jetson Orin</p>
""")
    
    # Timestamp
    html_parts.append(f"<div class='timestamp'>Gerado em: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</div>")
    
    # Stats summary
    if summary_rows:
        envs = {}
        for row in summary_rows:
            env = row.get('environment', '').strip()
            if env not in envs:
                envs[env] = {'count': 0, 'total_mean': [], 'slm_mean': []}
            envs[env]['count'] += 1
            try:
                total = float(row.get('total_s_mean', 0) or 0)
                slm = float(row.get('slm_per_diag_mean', 0) or 0)
                if total > 0:
                    envs[env]['total_mean'].append(total)
                if slm > 0:
                    envs[env]['slm_mean'].append(slm)
            except:
                pass
        
        html_parts.append("""
        <h2>Resumo Geral</h2>
        <div class='summary-box'>
            <table>
                <tr>
                    <th>Ambiente</th>
                    <th>Execuções</th>
                    <th>Latência Total (média)</th>
                    <th>SLM por Diagnóstico (média)</th>
                </tr>
        """)
        for env_name in ['desktop-legion', 'jetson-nano', 'jetson-orin']:
            if env_name in envs:
                env_data = envs[env_name]
                total_avg = sum(env_data['total_mean']) / len(env_data['total_mean']) if env_data['total_mean'] else 0
                slm_avg = sum(env_data['slm_mean']) / len(env_data['slm_mean']) if env_data['slm_mean'] else 0
                
                class_name = f'env-{env_name.split("-")[-1]}'
                html_parts.append(f"""
                <tr class='{class_name}'>
                    <td>{env_name}</td>
                    <td>{env_data['count']}</td>
                    <td>{total_avg:.3f}s</td>
                    <td>{slm_avg:.3f}s</td>
                </tr>
                """)
        html_parts.append("</table></div>")
    
    # Detailed summary table
    html_parts.append("""
        <h2>Detalhes por Modelo e Batch</h2>
        <table>
            <tr>
                <th>Ambiente</th>
                <th>Modelo</th>
                <th>Batch</th>
                <th>Execuções</th>
                <th>Latência Total (s)</th>
                <th>SLM/Diag (s)</th>
                <th>PDI/Imagem (ms)</th>
                <th>Acurácia</th>
                <th>Meta Atingida</th>
            </tr>
    """)
    
    for row in summary_rows:
        env = row.get('environment', '').strip()
        class_prefix = 'env-' + env.split('-')[-1] if '-' in env else 'env-' + env
        
        html_parts.append(f"""
        <tr>
            <td class='{class_prefix}'>{env}</td>
            <td>{row.get('model', '-')}</td>
            <td>{row.get('batch', '-')}</td>
            <td>{row.get('runs', '-')}</td>
            <td>{row.get('total_s_mean', '-')}</td>
            <td>{row.get('slm_per_diag_mean', '-')}</td>
            <td>{row.get('pdi_per_image_ms_mean', '-')}</td>
            <td>{row.get('accuracy_mean', '-')}</td>
            <td>{row.get('target_met_rate', '-')}</td>
        </tr>
        """)
    
    html_parts.append("</table>")
    
    # Speedup comparison
    if speedup_rows:
        html_parts.append("""
        <h2>Speedup vs Desktop Legion (Baseline)</h2>
        <div class='summary-box'>
            <p>Valores menores que 1.0 indicam que o ambiente é mais rápido que Desktop Legion (melhor).</p>
            <p>Valores maiores que 1.0 indicam que o ambiente é mais lento que Desktop Legion.</p>
        </div>
        <table>
            <tr>
                <th>Modelo</th>
                <th>Batch</th>
                <th>Jetson Orin Total Speedup</th>
                <th>Jetson Orin SLM Speedup</th>
                <th>Jetson Nano Total Speedup</th>
                <th>Jetson Nano SLM Speedup</th>
            </tr>
        """)
        
        for row in speedup_rows:
            orin_total = row.get('jetson-orin_speedup_vs_legion_total_x', '-')
            orin_slm = row.get('jetson-orin_speedup_vs_legion_slm_x', '-')
            nano_total = row.get('jetson-nano_speedup_vs_legion_total_x', '-')
            nano_slm = row.get('jetson-nano_speedup_vs_legion_slm_x', '-')
            
            html_parts.append(f"""
            <tr>
                <td>{row.get('model', '-')}</td>
                <td>{row.get('batch', '-')}</td>
                <td>{orin_total}</td>
                <td>{orin_slm}</td>
                <td>{nano_total}</td>
                <td>{nano_slm}</td>
            </tr>
            """)
        
        html_parts.append("</table>")
    
    # Plots section
    plots_dir = Path("outputs/benchmark_comparison/plots")
    if plots_dir.exists():
        plot_files = list(plots_dir.glob("*.png"))
        if plot_files:
            html_parts.append("""
            <h2>Visualizações</h2>
            """)
            
            plot_descriptions = {
                "boxplot_total_s_by_environment.png": "Distribuição de latência total por ambiente",
                "bar_slm_per_diag_mean.png": "Latência SLM média por diagnóstico",
                "line_total_s_mean_by_batch.png": "Tendência de latência por batch",
                "bar_speedup_vs_legion.png": "Speedup vs Desktop Legion",
                "bar_legend_speedup_total.png": "Comparação de speedup",
            }
            
            for plot_file in sorted(plot_files):
                desc = plot_descriptions.get(plot_file.name, plot_file.name)
                plot_rel_path = f"plots/{plot_file.name}"
                html_parts.append(f"""
            <div class='image-section'>
                <h3>{desc}</h3>
                <img src='{plot_rel_path}' alt='{desc}'>
            </div>
            """)
    
    html_parts.append("""
    </div>
</body>
</html>
    """)
    
    # Write HTML file
    html_content = "\n".join(html_parts)
    html_path = out_dir / "benchmark_report.html"
    html_path.write_text(html_content, encoding='utf-8')
    print(f"Relatório HTML gerado: {html_path}")


if __name__ == "__main__":
    out_dir = Path("outputs/benchmark_comparison")
    out_dir.mkdir(parents=True, exist_ok=True)
    generate_html_report(out_dir)
