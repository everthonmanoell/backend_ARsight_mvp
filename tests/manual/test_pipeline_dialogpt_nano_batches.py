"""
Manual benchmark runner for Jetson Nano using local DialoGPT.

Runs 6 predefined batches, 5 executions per batch, and saves
pipeline_test_*.json in the same style used by manual pipeline tests.

Usage:
    poetry run python tests/manual/test_pipeline_dialogpt_nano_batches.py
    poetry run python tests/manual/test_pipeline_dialogpt_nano_batches.py --runs 5
    poetry run python tests/manual/test_pipeline_dialogpt_nano_batches.py --device cuda
    
    ou sem poetry (se env já está ativado):
    python tests/manual/test_pipeline_dialogpt_nano_batches.py --runs 5 --device cuda
"""

import argparse
import copy
import json
import os
import platform
import sys
import tempfile
import time
from datetime import datetime
from pathlib import Path

import yaml
from PIL import Image

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.config.config import Config
from app.pipeline.illumination_pipeline import IlluminationPipeline


DIALOGPT_LOCAL_PATH = "/home/das9/models/DialoGPT-small"
BASE_CONFIG_PATH = Path("app/config/thresholds.yaml")

BATCHES = {
    "batch1": [
        ("data/uploads/20260315_143220/frame_00.jpg", "adequate"),
        ("data/uploads/20260315_143220/frame_01.jpg", "adequate"),
        ("data/uploads/20260315_143220/frame_02.jpg", "acceptable"),
        ("data/uploads/20260315_143220/frame_03.jpg", "acceptable"),
        ("data/uploads/20260315_143220/frame_04.jpg", "acceptable"),
        ("data/uploads/20260315_143220/frame_05.jpg", "adequate"),
        ("data/uploads/20260315_143220/frame_06.jpg", "adequate"),
        ("data/uploads/20260315_143220/frame_07.jpg", "adequate"),
        ("data/uploads/20260315_143220/frame_08.jpg", "adequate"),
        ("data/uploads/20260315_143220/frame_09.jpg", "adequate"),
    ],
    "batch2": [
        ("data/uploads/20260315_143447/frame_00.jpg", "acceptable"),
        ("data/uploads/20260315_143447/frame_01.jpg", "acceptable"),
        ("data/uploads/20260315_143447/frame_02.jpg", "acceptable"),
        ("data/uploads/20260315_143447/frame_03.jpg", "acceptable"),
        ("data/uploads/20260315_143447/frame_04.jpg", "acceptable"),
        ("data/uploads/20260315_143447/frame_05.jpg", "acceptable"),
        ("data/uploads/20260315_143447/frame_06.jpg", "acceptable"),
        ("data/uploads/20260315_143447/frame_07.jpg", "underexposed"),
        ("data/uploads/20260315_143447/frame_08.jpg", "acceptable"),
        ("data/uploads/20260315_143447/frame_09.jpg", "acceptable"),
    ],
    "batch3": [
        ("data/uploads/20260315_143615/frame_00.jpg", "adequate"),
        ("data/uploads/20260315_143615/frame_01.jpg", "adequate"),
        ("data/uploads/20260315_143615/frame_02.jpg", "adequate"),
        ("data/uploads/20260315_143615/frame_03.jpg", "adequate"),
        ("data/uploads/20260315_143615/frame_04.jpg", "adequate"),
        ("data/uploads/20260315_143615/frame_05.jpg", "adequate"),
        ("data/uploads/20260315_143615/frame_06.jpg", "adequate"),
        ("data/uploads/20260315_143615/frame_07.jpg", "adequate"),
        ("data/uploads/20260315_143615/frame_08.jpg", "adequate"),
        ("data/uploads/20260315_143615/frame_09.jpg", "overexposed"),
    ],
    "batch4": [
        ("data/uploads/20260315_143747/frame_00.jpg", "adequate"),
        ("data/uploads/20260315_143747/frame_01.jpg", "adequate"),
        ("data/uploads/20260315_143747/frame_02.jpg", "adequate"),
        ("data/uploads/20260315_143747/frame_03.jpg", "adequate"),
        ("data/uploads/20260315_143747/frame_04.jpg", "adequate"),
        ("data/uploads/20260315_143747/frame_05.jpg", "adequate"),
        ("data/uploads/20260315_143747/frame_06.jpg", "adequate"),
        ("data/uploads/20260315_143747/frame_07.jpg", "adequate"),
        ("data/uploads/20260315_143747/frame_08.jpg", "adequate"),
        ("data/uploads/20260315_143747/frame_09.jpg", "acceptable"),
    ],
    "batch5": [
        ("data/uploads/20260315_175638/frame_00.jpg", "underexposed"),
        ("data/uploads/20260315_175638/frame_01.jpg", "underexposed"),
        ("data/uploads/20260315_175638/frame_02.jpg", "underexposed"),
        ("data/uploads/20260315_175638/frame_03.jpg", "underexposed"),
        ("data/uploads/20260315_175638/frame_04.jpg", "underexposed"),
        ("data/uploads/20260315_175638/frame_05.jpg", "underexposed"),
        ("data/uploads/20260315_175638/frame_06.jpg", "underexposed"),
        ("data/uploads/20260315_175638/frame_07.jpg", "underexposed"),
        ("data/uploads/20260315_175638/frame_08.jpg", "underexposed"),
        ("data/uploads/20260315_175638/frame_09.jpg", "underexposed"),
    ],
    "batch6": [
        ("data/uploads/20260315_180200/frame_00.jpg", "adequate"),
        ("data/uploads/20260315_180200/frame_01.jpg", "adequate"),
        ("data/uploads/20260315_180200/frame_02.jpg", "adequate"),
        ("data/uploads/20260315_180200/frame_03.jpg", "adequate"),
        ("data/uploads/20260315_180200/frame_04.jpg", "adequate"),
        ("data/uploads/20260315_180200/frame_05.jpg", "adequate"),
        ("data/uploads/20260315_180200/frame_06.jpg", "underexposed"),
        ("data/uploads/20260315_180200/frame_07.jpg", "underexposed"),
        ("data/uploads/20260315_180200/frame_08.jpg", "underexposed"),
        ("data/uploads/20260315_180200/frame_09.jpg", "underexposed"),
    ],
}


def detect_environment() -> str:
    machine = platform.machine()
    if machine == "aarch64":
        try:
            with open("/etc/nv_tegra_release", "r", encoding="utf-8") as f:
                release_info = f.read()
                if "R32" in release_info:
                    return "jetson-nano"
                if "R36" in release_info:
                    return "jetson-orin"
                return "jetson"
        except (FileNotFoundError, OSError):
            return "jetson"
    return "desktop-legion"


def sep(char: str = "-", width: int = 120) -> None:
    print(char * width)


def load_image(path_str: str):
    path = Path(path_str)
    if path.exists():
        return Image.open(path)

    app_path = Path("/app") / path_str
    if app_path.exists():
        return Image.open(app_path)

    cwd_path = Path.cwd() / path_str
    if cwd_path.exists():
        return Image.open(cwd_path)

    return None


def build_dialogpt_config(base_config: Path, model_path: str, device: str) -> str:
    with open(base_config, "r", encoding="utf-8") as f:
        config_data = yaml.safe_load(f)

    cfg = copy.deepcopy(config_data)
    cfg.setdefault("models", {})
    cfg["models"]["default"] = "dialogpt-small"
    cfg["models"]["use_4bit"] = False
    cfg["models"]["greedy_decoding"] = True
    cfg["models"]["device"] = device

    cfg["models"].setdefault("dialogpt-small", {})
    cfg["models"]["dialogpt-small"]["name"] = model_path

    temp_file = tempfile.NamedTemporaryFile(mode="w", suffix="_dialogpt_nano.yaml", delete=False, encoding="utf-8")
    with temp_file:
        yaml.safe_dump(cfg, temp_file, allow_unicode=True, sort_keys=False)

    return temp_file.name


def run_single_pipeline(batch_name: str, batch_images: list, run_index: int, output_base: Path, device: str) -> dict:
    config = Config()
    model_type = config.get("models.default", "dialogpt-small")
    use_4bit = config.get("models.use_4bit", False)

    print(f"\n[{batch_name}] Run {run_index} | model={model_type} | 4bit={use_4bit} | device={device}")

    t_init = time.perf_counter()
    pipeline = IlluminationPipeline(model_type=model_type, use_4bit=use_4bit, device=device)
    pipeline._load_model()
    init_elapsed = time.perf_counter() - t_init

    images = []
    filenames = []
    expected_labels = []
    missing = []

    for path_str, label in batch_images:
        img = load_image(path_str)
        path = Path(path_str)
        if img is None:
            missing.append(path_str)
            continue
        images.append(img)
        filenames.append(path.name)
        expected_labels.append(label)

    if missing:
        print(f"  [warn] {len(missing)} image(s) missing in {batch_name}")

    if not images:
        raise RuntimeError(f"No images loaded for {batch_name}")

    n = len(images)

    t_pdi = time.perf_counter()
    pdi_metrics = pipeline.extract_metrics_batch(images)
    pdi_elapsed = time.perf_counter() - t_pdi

    t_slm = time.perf_counter()
    diagnoses, summary = pipeline.diagnose_from_metrics_batch_with_summary(pdi_metrics)
    slm_elapsed = time.perf_counter() - t_slm

    per_diag = slm_elapsed / n
    total_elapsed = pdi_elapsed + slm_elapsed

    correct = 0
    frames = []

    for i, (fname, pdi, diag, expected) in enumerate(zip(filenames, pdi_metrics, diagnoses, expected_labels)):
        predicted = pdi["illumination_label"]
        is_correct = predicted == expected
        if is_correct:
            correct += 1

        frames.append(
            {
                "frame_index": i,
                "filename": fname,
                "expected_label": expected,
                "status": diag["status"],
                "risk_level": diag["risk_level"],
                "label_correct": is_correct,
                "explanation": diag["explanation"],
                "triggered_rules": diag.get("triggered_rules", []),
                "recommendations": diag.get("recommendations", []),
                "metrics": {
                    "illumination_score": round(pdi["illumination"], 4),
                    "illumination_label": pdi["illumination_label"],
                    "mean_brightness": round(pdi["mean_luma"] / 255.0, 4),
                    "mean_luma": round(pdi["mean_luma"], 2),
                    "std_luma": round(pdi["std_luma"], 2),
                    "uniformity": round(pdi["uniformity"], 4),
                    "pct_clipped_dark": round(pdi["pct_clipped_dark"], 4),
                    "pct_clipped_bright": round(pdi["pct_clipped_bright"], 4),
                },
            }
        )

    accuracy = correct / n * 100
    meta_ok = per_diag < 1.0

    env = detect_environment()
    out_dir = output_base / batch_name
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / f"pipeline_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

    output = {
        "metadata": {
            "timestamp": datetime.now().isoformat(),
            "environment": env,
            "model": model_type,
            "device": device,
            "quantization": "4-bit" if use_4bit else "fp16/fp32",
            "batch_size": n,
            "batch_folder": batch_name,
            "run_index": run_index,
            "model_path": DIALOGPT_LOCAL_PATH,
        },
        "performance": {
            "init_s": round(init_elapsed, 3),
            "pdi_total_ms": round(pdi_elapsed * 1000, 1),
            "pdi_per_image_ms": round((pdi_elapsed / n) * 1000, 1),
            "slm_total_s": round(slm_elapsed, 3),
            "slm_per_diagnosis_s": round(per_diag, 3),
            "total_s": round(total_elapsed, 3),
            "target_met": meta_ok,
        },
        "statistics": {
            "total": n,
            "correct": correct,
            "accuracy": round(accuracy, 2),
        },
        "summary": summary,
        "frames": frames,
    }

    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(
        f"  saved={out_file} | pdi={pdi_elapsed*1000:.1f}ms | "
        f"slm={slm_elapsed:.2f}s ({per_diag*1000:.0f}ms/diag) | accuracy={accuracy:.1f}%"
    )

    return {
        "batch": batch_name,
        "run": run_index,
        "file": str(out_file),
        "slm_per_diag_s": per_diag,
        "accuracy": accuracy,
        "target_met": meta_ok,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run Jetson Nano benchmark with local DialoGPT")
    parser.add_argument("--runs", type=int, default=5, help="Executions per batch")
    parser.add_argument("--device", default="cuda", choices=["cuda", "cpu", "auto"], help="Inference device")
    parser.add_argument("--model-path", default=DIALOGPT_LOCAL_PATH, help="Local DialoGPT model path")
    parser.add_argument("--output-base", default="outputs/jetson-nano", help="Base output dir")
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    if args.runs < 1:
        raise ValueError("--runs must be >= 1")

    if not Path(args.model_path).exists():
        raise FileNotFoundError(f"DialoGPT local path not found: {args.model_path}")

    sep("=")
    print("JETSON NANO BENCHMARK - DIALOGPT LOCAL (6 BATCHES)")
    print(f"model_path={args.model_path}")
    print(f"runs_per_batch={args.runs}")
    print(f"output_base={args.output_base}")
    sep("=")

    custom_config_path = build_dialogpt_config(BASE_CONFIG_PATH, args.model_path, args.device)
    os.environ["AR_CONFIG_FILE"] = custom_config_path

    cfg = Config()
    cfg.load_config(custom_config_path)

    output_base = Path(args.output_base)
    all_results = []

    try:
        for batch_name, batch_images in BATCHES.items():
            sep()
            print(f"Running {batch_name} ({len(batch_images)} images)")
            sep()
            for run_idx in range(1, args.runs + 1):
                result = run_single_pipeline(
                    batch_name=batch_name,
                    batch_images=batch_images,
                    run_index=run_idx,
                    output_base=output_base,
                    device=args.device,
                )
                all_results.append(result)
    finally:
        try:
            os.remove(custom_config_path)
        except OSError:
            pass

    sep("=")
    print("FINAL SUMMARY")
    sep("=")
    target_hits = sum(1 for r in all_results if r["target_met"])
    print(f"total_runs={len(all_results)}")
    print(f"target_met_runs={target_hits}/{len(all_results)}")

    by_batch = {}
    for row in all_results:
        by_batch.setdefault(row["batch"], []).append(row)

    for batch_name in sorted(by_batch.keys()):
        rows = by_batch[batch_name]
        avg_diag = sum(r["slm_per_diag_s"] for r in rows) / len(rows)
        avg_acc = sum(r["accuracy"] for r in rows) / len(rows)
        print(f"{batch_name}: avg_slm_per_diag={avg_diag:.3f}s | avg_accuracy={avg_acc:.1f}%")


if __name__ == "__main__":
    main()
