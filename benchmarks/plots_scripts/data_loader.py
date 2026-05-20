"""
Benchmark data loader for aggregating results from JSON files.

Expected structure:
- outputs/
  - jetson-nano/batch{1-6}/{dialogpt,qwen}/pipeline_test_*.json
  - jetson-orin/batch{1-6}/{dialogpt,qwen,phi}/pipeline_test_*.json
  - desktop-legion/batch{1-6}/{dialogpt,phi,qwen}/pipeline_test_*.json
"""

import json
from collections import defaultdict
from pathlib import Path
from statistics import mean, median, stdev
from typing import Any, Dict, List, Optional


class BenchmarkLoader:
    """Load and aggregate benchmark results from the outputs directory."""

    def __init__(self, outputs_base: Path = Path("outputs")):
        self.outputs_base = outputs_base
        self.data = []  # List of benchmark records.
        self._load_all()

    def _load_all(self) -> None:
        """Load all benchmark JSON files."""
        self.data = []

        # Environment directories.
        env_dirs = list(self.outputs_base.glob("jetson-*")) + list(
            self.outputs_base.glob("desktop-*")
        )

        for env_dir in env_dirs:
            if env_dir.name in ["legacy", "batch_*"]:
                continue

            env = env_dir.name  # Examples: jetson-nano, jetson-orin, desktop-legion.

            # Batch directories.
            for batch_dir in sorted(env_dir.glob("batch*")):
                batch_name = batch_dir.name

                # Model directories, such as dialogpt, qwen, qwen-cpu, qwen-gpu, or phi.
                model_dirs = list(batch_dir.glob("*"))

                if not model_dirs or batch_dir.is_file():
                    # Fallback: JSON files directly inside the batch directory, used by older output structures.
                    for json_file in batch_dir.glob("pipeline_test_*.json"):
                        record = self._load_json(
                            json_file,
                            env,
                            batch_name,
                            model="unknown",
                        )

                        if record:
                            self.data.append(record)

                else:
                    # JSON files inside model-specific directories.
                    for model_dir in model_dirs:
                        if not model_dir.is_dir():
                            continue

                        model = model_dir.name

                        for json_file in model_dir.glob("pipeline_test_*.json"):
                            record = self._load_json(
                                json_file,
                                env,
                                batch_name,
                                model,
                            )

                            if record:
                                self.data.append(record)

    def _load_json(
        self,
        json_path: Path,
        env: str,
        batch: str,
        model: str,
    ) -> Optional[Dict[str, Any]]:
        """Load a single benchmark JSON file."""
        try:
            with open(json_path, "r", encoding="utf-8") as file:
                raw = json.load(file)

        except Exception as exc:
            print(f"Error loading {json_path}: {exc}")
            return None

        metadata = raw.get("metadata", {})
        perf = raw.get("performance", {})
        stats = raw.get("statistics", {})

        # Detect model from file metadata when it was not provided by the path.
        if model == "unknown":
            model = str(metadata.get("model", "unknown")).lower()

        return {
            "environment": env,
            "batch": batch,
            "model": model,
            "timestamp": metadata.get("timestamp"),
            "run_index": metadata.get("run_index", 0),
            "device": metadata.get("device", "unknown"),
            "quantization": metadata.get("quantization", "unknown"),

            # Performance metrics.
            "init_s": float(perf.get("init_s", 0)),
            "pdi_total_ms": float(perf.get("pdi_total_ms", 0)),
            "pdi_per_image_ms": float(perf.get("pdi_per_image_ms", 0)),
            "slm_total_s": float(perf.get("slm_total_s", 0)),
            "slm_per_diagnosis_s": float(perf.get("slm_per_diagnosis_s", 0)),
            "total_s": float(perf.get("total_s", 0)),
            "target_met": bool(perf.get("target_met", False)),

            # Quality metrics.
            "accuracy": float(stats.get("accuracy", 0)),
            "correct": int(stats.get("correct", 0)),
            "total": int(stats.get("total", 10)),
        }

    def aggregated(self) -> Dict[str, Dict[str, List[float]]]:
        """Aggregate metrics by (environment, model, batch)."""
        agg = defaultdict(lambda: defaultdict(list))

        for record in self.data:
            key = (record["environment"], record["model"], record["batch"])

            agg[key]["slm_per_diag"].append(record["slm_per_diagnosis_s"])
            agg[key]["accuracy"].append(record["accuracy"])
            agg[key]["total_s"].append(record["total_s"])
            agg[key]["pdi_per_image_ms"].append(record["pdi_per_image_ms"])
            agg[key]["target_met_count"].append(1 if record["target_met"] else 0)

        return agg

    def summary_by_env_model(self) -> List[Dict[str, Any]]:
        """Return a global summary grouped by (environment, model)."""
        summary = defaultdict(lambda: defaultdict(list))

        for record in self.data:
            key = (record["environment"], record["model"])

            summary[key]["slm_per_diag"].append(record["slm_per_diagnosis_s"])
            summary[key]["accuracy"].append(record["accuracy"])
            summary[key]["total_s"].append(record["total_s"])

        result = []

        for (env, model), metrics in sorted(summary.items()):
            slm_vals = metrics["slm_per_diag"]
            acc_vals = metrics["accuracy"]
            total_vals = metrics["total_s"]

            result.append(
                {
                    "environment": env,
                    "model": model,
                    "runs": len(slm_vals),
                    "slm_per_diag_mean": mean(slm_vals),
                    "slm_per_diag_median": median(slm_vals),
                    "slm_per_diag_std": stdev(slm_vals) if len(slm_vals) > 1 else 0,
                    "accuracy_mean": mean(acc_vals),
                    "total_s_mean": mean(total_vals),
                }
            )

        return result

    def filter_by_env(self, env: str) -> List[Dict[str, Any]]:
        """Filter records by environment."""
        return [record for record in self.data if record["environment"] == env]

    def filter_by_model(self, model: str) -> List[Dict[str, Any]]:
        """Filter records by model."""
        return [
            record
            for record in self.data
            if record["model"].lower() == model.lower()
        ]

    def filter_by_env_model(self, env: str, model: str) -> List[Dict[str, Any]]:
        """Filter records by environment and model."""
        return [
            record
            for record in self.data
            if record["environment"] == env
            and record["model"].lower() == model.lower()
        ]

    def stats(self) -> Dict[str, Any]:
        """Return global benchmark statistics."""
        if not self.data:
            return {}

        return {
            "total_runs": len(self.data),
            "environments": sorted(set(record["environment"] for record in self.data)),
            "models": sorted(set(record["model"] for record in self.data)),
            "batches": sorted(set(record["batch"] for record in self.data)),
            "avg_slm_per_diag": mean(
                record["slm_per_diagnosis_s"] for record in self.data
            ),
            "avg_accuracy": mean(record["accuracy"] for record in self.data),
            "target_met_rate": sum(
                1 for record in self.data if record["target_met"]
            )
            / len(self.data),
        }


if __name__ == "__main__":
    loader = BenchmarkLoader(Path("../../outputs"))
    stats = loader.stats()

    print("Benchmark Statistics")
    print(f"  Total runs: {stats.get('total_runs', 0)}")
    print(f"  Environments: {stats.get('environments', [])}")
    print(f"  Models: {stats.get('models', [])}")
    print(f"  Avg SLM per diag: {stats.get('avg_slm_per_diag', 0):.3f}s")
    print(f"  Avg accuracy: {stats.get('avg_accuracy', 0):.1f}%")
    print(f"  Target met rate: {stats.get('target_met_rate', 0) * 100:.1f}%")