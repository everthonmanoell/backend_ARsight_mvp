import argparse
import csv
import json
import math
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from statistics import mean, median
from typing import Any


def find_json_files(base_dir: Path) -> list[Path]:
    if not base_dir.exists():
        return []
    return sorted(base_dir.rglob("pipeline_test_*.json"))


def safe_float(value: Any) -> float | None:
    try:
        if value is None:
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def percentile(values: list[float], p: float) -> float | None:
    if not values:
        return None
    if len(values) == 1:
        return values[0]
    sorted_values = sorted(values)
    k = (len(sorted_values) - 1) * (p / 100)
    f = math.floor(k)
    c = math.ceil(k)
    if f == c:
        return sorted_values[int(k)]
    d0 = sorted_values[f] * (c - k)
    d1 = sorted_values[c] * (k - f)
    return d0 + d1


def stddev(values: list[float]) -> float | None:
    if len(values) <= 1:
        return 0.0 if values else None
    m = mean(values)
    return (sum((x - m) ** 2 for x in values) / (len(values) - 1)) ** 0.5


def extract_batch_name(path: Path, metadata: dict[str, Any]) -> str:
    for part in path.parts:
        if part.lower().startswith("batch"):
            return part.lower()
    folder = metadata.get("batch_folder")
    if folder:
        return str(folder)
    return "unknown"


def load_record(path: Path, env_fallback: str) -> dict[str, Any] | None:
    try:
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, json.JSONDecodeError):
        return None

    metadata = data.get("metadata", {})
    perf = data.get("performance", {})
    stats = data.get("statistics", {})

    env = str(metadata.get("environment") or env_fallback).lower()
    model = str(metadata.get("model") or "unknown").lower()
    batch_name = extract_batch_name(path, metadata)

    ts = metadata.get("timestamp")
    parsed_ts = None
    if isinstance(ts, str):
        try:
            parsed_ts = datetime.fromisoformat(ts)
        except ValueError:
            parsed_ts = None

    return {
        "file": str(path).replace("\\", "/"),
        "run_id": path.stem,
        "timestamp": parsed_ts.isoformat() if parsed_ts else "",
        "environment": env,
        "model": model,
        "batch": batch_name,
        "batch_size": safe_float(metadata.get("batch_size")),
        "quantization": str(metadata.get("quantization") or ""),
        "device": str(metadata.get("device") or ""),
        "total_s": safe_float(perf.get("total_s")),
        "slm_total_s": safe_float(perf.get("slm_total_s")),
        "slm_per_diagnosis_s": safe_float(perf.get("slm_per_diagnosis_s")),
        "pdi_total_ms": safe_float(perf.get("pdi_total_ms")),
        "pdi_per_image_ms": safe_float(perf.get("pdi_per_image_ms")),
        "target_met": bool(perf.get("target_met")) if perf.get("target_met") is not None else False,
        "accuracy": safe_float(stats.get("accuracy")),
        "correct": safe_float(stats.get("correct")),
        "total_samples": safe_float(stats.get("total")),
    }


def collect_records(desktop_legion_dir: Path, jetson_nano_dir: Path, jetson_orin_dir: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []

    for path in find_json_files(desktop_legion_dir):
        record = load_record(path, env_fallback="desktop-legion")
        if record:
            records.append(record)

    for path in find_json_files(jetson_nano_dir):
        record = load_record(path, env_fallback="jetson-nano")
        if record:
            records.append(record)

    for path in find_json_files(jetson_orin_dir):
        record = load_record(path, env_fallback="jetson-orin")
        if record:
            records.append(record)

    return records


def metric_summary(values: list[float]) -> dict[str, float | None]:
    return {
        "n": len(values),
        "mean": mean(values) if values else None,
        "median": median(values) if values else None,
        "std": stddev(values),
        "min": min(values) if values else None,
        "max": max(values) if values else None,
        "p95": percentile(values, 95),
    }


def aggregate_records(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for rec in records:
        key = (rec["environment"], rec["model"], rec["batch"])
        grouped[key].append(rec)

    aggregates: list[dict[str, Any]] = []
    for (env, model, batch), rows in sorted(grouped.items()):
        total_vals = [r["total_s"] for r in rows if isinstance(r["total_s"], float)]
        slm_vals = [r["slm_per_diagnosis_s"] for r in rows if isinstance(r["slm_per_diagnosis_s"], float)]
        pdi_vals = [r["pdi_per_image_ms"] for r in rows if isinstance(r["pdi_per_image_ms"], float)]
        acc_vals = [r["accuracy"] for r in rows if isinstance(r["accuracy"], float)]

        total_sum = metric_summary(total_vals)
        slm_sum = metric_summary(slm_vals)
        pdi_sum = metric_summary(pdi_vals)
        acc_sum = metric_summary(acc_vals)

        target_true = sum(1 for r in rows if r.get("target_met") is True)

        aggregates.append(
            {
                "environment": env,
                "model": model,
                "batch": batch,
                "runs": len(rows),
                "target_met_runs": target_true,
                "target_met_rate": (target_true / len(rows)) * 100.0 if rows else 0.0,
                "total_s_mean": total_sum["mean"],
                "total_s_median": total_sum["median"],
                "total_s_p95": total_sum["p95"],
                "slm_per_diag_mean": slm_sum["mean"],
                "slm_per_diag_median": slm_sum["median"],
                "slm_per_diag_p95": slm_sum["p95"],
                "pdi_per_image_ms_mean": pdi_sum["mean"],
                "accuracy_mean": acc_sum["mean"],
                "accuracy_min": acc_sum["min"],
            }
        )

    return aggregates


def build_speedup(aggregates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_model_batch: dict[tuple[str, str], dict[str, dict[str, Any]]] = defaultdict(dict)
    for row in aggregates:
        key = (row["model"], row["batch"])
        by_model_batch[key][row["environment"]] = row

    speedups: list[dict[str, Any]] = []
    for (model, batch), env_rows in sorted(by_model_batch.items()):
        # Require at least 2 environments for comparison
        if len(env_rows) < 2:
            continue

        base_envs = ["desktop-legion", "jetson-nano", "jetson-orin"]
        available_envs = [e for e in base_envs if e in env_rows]
        
        if len(available_envs) < 2:
            continue

        speedup_row: dict[str, Any] = {
            "model": model,
            "batch": batch,
        }

        # Add metrics for each environment
        for env in available_envs:
            env_data = env_rows[env]
            speedup_row[f"{env}_total_mean_s"] = env_data.get("total_s_mean")
            speedup_row[f"{env}_slm_per_diag_mean_s"] = env_data.get("slm_per_diag_mean")

        # Calculate speedups relative to desktop-legion (baseline)
        if "desktop-legion" in env_rows:
            baseline = env_rows["desktop-legion"]
            baseline_total = baseline.get("total_s_mean")
            baseline_slm = baseline.get("slm_per_diag_mean")

            for env in available_envs:
                if env == "desktop-legion":
                    continue
                env_data = env_rows[env]
                env_total = env_data.get("total_s_mean")
                env_slm = env_data.get("slm_per_diag_mean")

                if baseline_total and env_total:
                    speedup_row[f"{env}_speedup_vs_legion_total_x"] = baseline_total / env_total
                if baseline_slm and env_slm:
                    speedup_row[f"{env}_speedup_vs_legion_slm_x"] = baseline_slm / env_slm

        speedups.append(speedup_row)

    return speedups


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return

    # Coletar todas as keys possíveis
    all_keys: set[str] = set()
    for row in rows:
        all_keys.update(row.keys())
    
    fieldnames = sorted(list(all_keys))
    
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, restval="")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def fmt(value: Any, digits: int = 3) -> str:
    if isinstance(value, (int, float)):
        return f"{value:.{digits}f}"
    if value is None:
        return "-"
    return str(value)


def write_markdown(path: Path, summary_rows: list[dict[str, Any]], speedup_rows: list[dict[str, Any]]) -> None:
    lines: list[str] = []
    lines.append("# Benchmark de Performance - Desktop Legion vs Jetson Nano vs Jetson Orin")
    lines.append("")
    lines.append(f"Gerado em: {datetime.now().isoformat(timespec='seconds')}")
    lines.append("")

    lines.append("## Resumo por ambiente/modelo/batch")
    lines.append("")
    lines.append("| environment | model | batch | runs | total_s_mean | slm_per_diag_mean | pdi_per_image_ms_mean | accuracy_mean | target_met_rate |")
    lines.append("|---|---|---:|---:|---:|---:|---:|---:|---:|")

    for row in summary_rows:
        lines.append(
            "| "
            + " | ".join(
                [
                    str(row.get("environment", "")),
                    str(row.get("model", "")),
                    str(row.get("batch", "")),
                    str(row.get("runs", "")),
                    fmt(row.get("total_s_mean")),
                    fmt(row.get("slm_per_diag_mean")),
                    fmt(row.get("pdi_per_image_ms_mean")),
                    fmt(row.get("accuracy_mean")),
                    fmt(row.get("target_met_rate"), digits=1) + "%",
                ]
            )
            + " |"
        )

    lines.append("")
    lines.append("## Speedup vs Desktop Legion")
    lines.append("")
    
    if speedup_rows:
        # Build dynamic headers based on what's in the first row
        first_row = speedup_rows[0]
        header_parts = ["model", "batch"]
        for key in sorted(first_row.keys()):
            if key not in ["model", "batch"] and "speedup" in key:
                header_parts.append(key)
        
        separator = "|" + "|".join(["---"] * len(header_parts)) + "|"
        header = "|" + "|".join(header_parts) + "|"
        
        lines.append(header)
        lines.append(separator)

        for row in speedup_rows:
            row_parts = [str(row.get("model", "")), str(row.get("batch", ""))]
            for key in sorted(first_row.keys()):
                if key not in ["model", "batch"] and "speedup" in key:
                    row_parts.append(fmt(row.get(key)))
            lines.append("|" + "|".join(row_parts) + "|")

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def try_generate_plots(records: list[dict[str, Any]], aggregates: list[dict[str, Any]], speedups: list[dict[str, Any]], out_dir: Path) -> str:
    try:
        import matplotlib.pyplot as plt  # type: ignore
    except ImportError:
        return "matplotlib nao instalado, graficos nao gerados"

    plots_dir = out_dir / "plots"
    plots_dir.mkdir(parents=True, exist_ok=True)

    # 1) Boxplot de latencia total por ambiente (3 ambientes)
    environments = ["desktop-legion", "jetson-nano", "jetson-orin"]
    env_data: dict[str, list[float]] = {}
    
    for env in environments:
        env_totals = [r["total_s"] for r in records if r["environment"] == env and isinstance(r.get("total_s"), float)]
        if env_totals:
            env_data[env] = env_totals

    if len(env_data) >= 2:
        plt.figure(figsize=(10, 5))
        data_to_plot = [env_data[env] for env in environments if env in env_data]
        labels = [env for env in environments if env in env_data]
        plt.boxplot(data_to_plot, tick_labels=labels, patch_artist=True)
        plt.title("Latencia total por ambiente")
        plt.ylabel("total_s")
        plt.grid(axis="y", linestyle="--", alpha=0.4)
        plt.xticks(rotation=15)
        plt.tight_layout()
        plt.savefig(plots_dir / "boxplot_total_s_by_environment.png", dpi=160)
        plt.close()

    # 2) Barra media slm por diagnostico por ambiente+modelo
    bar_rows = [r for r in aggregates if isinstance(r.get("slm_per_diag_mean"), float)]
    if bar_rows:
        labels = [f"{r['environment']}:{r['model']}:{r['batch']}" for r in bar_rows]
        values = [r["slm_per_diag_mean"] for r in bar_rows]

        plt.figure(figsize=(max(12, len(labels) * 0.5), 5))
        colors = []
        for label in labels:
            if "desktop-legion" in label:
                colors.append("#1f77b4")  # blue
            elif "jetson-nano" in label:
                colors.append("#ff7f0e")  # orange
            else:
                colors.append("#2ca02c")  # green
        
        plt.bar(range(len(labels)), values, color=colors)
        plt.xticks(range(len(labels)), labels, rotation=75, ha="right")
        plt.ylabel("slm_per_diagnosis_s (media)")
        plt.title("SLM medio por diagnostico por ambiente/modelo")
        plt.grid(axis="y", linestyle="--", alpha=0.4)
        plt.tight_layout()
        plt.savefig(plots_dir / "bar_slm_per_diag_mean.png", dpi=160)
        plt.close()

    # 3) Linha por batch comparando total medio
    chart_rows = [r for r in aggregates if isinstance(r.get("total_s_mean"), float)]
    if chart_rows:
        series: dict[str, list[tuple[int, float]]] = defaultdict(list)
        for row in chart_rows:
            batch = str(row.get("batch", ""))
            digits = "".join(ch for ch in batch if ch.isdigit())
            if not digits:
                continue
            batch_n = int(digits)
            key = f"{row['environment']}:{row['model']}"
            series[key].append((batch_n, row["total_s_mean"]))

        if series:
            plt.figure(figsize=(10, 6))
            for key, points in sorted(series.items()):
                points = sorted(points, key=lambda x: x[0])
                xs = [p[0] for p in points]
                ys = [p[1] for p in points]
                plt.plot(xs, ys, marker="o", label=key)
            plt.xlabel("batch")
            plt.ylabel("total_s_mean")
            plt.title("Tendencia de latencia total media por batch")
            plt.grid(True, linestyle="--", alpha=0.4)
            plt.legend(fontsize=9)
            plt.tight_layout()
            plt.savefig(plots_dir / "line_total_s_mean_by_batch.png", dpi=160)
            plt.close()

    # 4) Speedup bars (dinâmico baseado no que está nos dados)
    if speedups:
        speed_rows = [r for r in speedups if any(isinstance(r.get(k), float) for k in r.keys() if "speedup" in k)]
        if speed_rows:
            # Pega o primeiro speedup para saber qual é a métrica
            first_speedup_col = None
            for k in speed_rows[0].keys():
                if "speedup" in k and "total" in k:
                    first_speedup_col = k
                    break
            
            if first_speedup_col:
                labels = [f"{r['model']}:{r['batch']}" for r in speed_rows]
                values = [r.get(first_speedup_col) for r in speed_rows]
                values = [v if isinstance(v, float) else 0 for v in values]

                plt.figure(figsize=(max(10, len(labels) * 0.5), 5))
                plt.bar(range(len(labels)), values, color="#2ca02c")
                plt.axhline(1.0, color="red", linestyle="--", linewidth=1)
                plt.xticks(range(len(labels)), labels, rotation=60, ha="right")
                plt.ylabel("speedup x (lower is faster)")
                plt.title("Speedup vs Desktop Legion (total_s_mean)")
                plt.grid(axis="y", linestyle="--", alpha=0.4)
                plt.tight_layout()
                plt.savefig(plots_dir / "bar_speedup_vs_legion.png", dpi=160)
                plt.close()

    return "ok"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Benchmark comparativo entre Desktop Legion, Jetson Nano e Jetson Orin")
    parser.add_argument("--desktop-legion-dir", default="outputs/desktop-legion", help="Diretorio raiz dos JSONs da Desktop Legion")
    parser.add_argument("--jetson-nano-dir", default="outputs/jetson-nano", help="Diretorio raiz dos JSONs da Jetson Nano")
    parser.add_argument("--jetson-orin-dir", default="outputs/jetson-orin", help="Diretorio raiz dos JSONs da Jetson Orin")
    parser.add_argument("--out-dir", default="outputs/benchmark_comparison", help="Diretorio de saida")
    parser.add_argument("--no-plots", action="store_true", help="Nao gerar graficos")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    records = collect_records(
        Path(args.desktop_legion_dir),
        Path(args.jetson_nano_dir),
        Path(args.jetson_orin_dir)
    )
    if not records:
        print("Nenhum arquivo de benchmark encontrado.")
        return

    aggregates = aggregate_records(records)
    speedups = build_speedup(aggregates)

    write_csv(out_dir / "runs_raw.csv", records)
    write_csv(out_dir / "summary_by_env_model_batch.csv", aggregates)
    write_csv(out_dir / "speedup_vs_desktop_legion.csv", speedups)
    write_markdown(out_dir / "benchmark_report.md", aggregates, speedups)

    plot_status = "skipped"
    if not args.no_plots:
        plot_status = try_generate_plots(records, aggregates, speedups, out_dir)

    print(f"Total de execucoes lidas: {len(records)}")
    print(f"Resumo agregado: {len(aggregates)} grupos")
    print(f"Comparacoes geradas: {len(speedups)}")
    print(f"Saida em: {out_dir}")
    print(f"Plots: {plot_status}")


if __name__ == "__main__":
    main()
