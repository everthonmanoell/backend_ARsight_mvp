# API Guide

This guide documents the REST API for illumination-based AR scene diagnosis. The API implements a two-step batch processing flow: images are uploaded first, then diagnosed in a separate request. This separation keeps PDI extraction and SLM inference independent, enabling better error isolation per frame.

For interactive documentation, start the API and open `http://localhost:8000/docs`.

---

## Processing Flow

```
POST /upload/batch
  -> validates and saves N images to disk
  -> returns batch_id

POST /diagnose/batch/{batch_id}
  -> loads saved images
  -> PDI: extracts illumination metrics per frame
  -> Rule Engine: deterministic status and risk classification
  -> SLM: batch explanation generation
  -> Output validation + template fallback if needed
  -> returns complete diagnosis JSON

GET /diagnose/batch/{batch_id}/status   -> check progress
GET /diagnose/batch/{batch_id}/result   -> retrieve saved result
```

---

## Endpoints

### GET `/`

Returns API version and available endpoints.

```bash
curl http://localhost:8000/
```

---

### GET `/health`

Returns API status and loaded model information.

```bash
curl http://localhost:8000/health
```

**Response (200 — healthy):**

```json
{
  "status": "healthy",
  "model": "qwen",
  "device": "cuda",
  "quantization": "4-bit"
}
```

**Response (503 — pipeline not initialized):**

```json
{
  "status": "unhealthy",
  "error": "Pipeline not initialized"
}
```

---

### POST `/upload/batch`

Validates and saves multiple images to disk. Returns a `batch_id` for later diagnosis.

Images are saved as `frame_00.jpg`, `frame_01.jpg`, etc., in `data/uploads/{batch_id}/`.

**Request:**

```bash
curl -X POST http://localhost:8000/upload/batch \
  -F "files=@frame_00.jpg" \
  -F "files=@frame_01.jpg" \
  -F "files=@frame_02.jpg"
```

**Response (200):**

```json
{
  "batch_id": "batch_20260416_200002_74ee64",
  "status": "uploaded",
  "files_saved": 3,
  "message": "Saved 3/3 files"
}
```

**Constraints (configurable in `thresholds.yaml`):**

- Max batch size: 10 images
- Max image size: 10 MB
- Allowed formats: jpg, jpeg, png, bmp

---

### POST `/diagnose/batch/{batch_id}`

Runs diagnosis on a previously uploaded batch. If the batch has already been diagnosed, returns the cached result.

```bash
curl -X POST http://localhost:8000/diagnose/batch/batch_20260416_200002_74ee64
```

**Response (200):**

```json
{
  "batch_id": "batch_20260416_200002_74ee64",
  "status": "completed",
  "metadata": {
    "timestamp": "2026-04-16T20:00:15.123456",
    "batch_id": "batch_20260416_200002_74ee64",
    "environment": "jetson-orin",
    "model": "qwen",
    "device": "cuda",
    "quantization": "fp32",
    "batch_size": 3
  },
  "performance": {
    "pdi_total_ms": 45.2,
    "pdi_per_image_ms": 15.1,
    "slm_total_s": 1.119,
    "slm_per_diagnosis_s": 0.373,
    "total_s": 1.164,
    "target_met": true
  },
  "statistics": {
    "total": 3,
    "correct": 3,
    "accuracy": 100.0
  },
  "summary": {
    "overall_risk": "high",
    "dominant_label": "underexposed",
    "problem_count": 1,
    "normal_count": 2,
    "explanation": "One frame shows insufficient lighting that may affect AR tracking.",
    "recommendations": [
      {
        "condition": "adequate_acceptable",
        "frames": [0, 2],
        "count": 2,
        "actions": []
      },
      {
        "condition": "underexposed",
        "frames": [1],
        "count": 1,
        "actions": ["Increase ambient lighting", "Avoid dark environments"]
      }
    ],
    "metrics_avg": {
      "mean_brightness": 0.5412,
      "mean_luma": 138.0,
      "uniformity": 0.7823,
      "pct_clipped_bright": 0.0021,
      "pct_clipped_dark": 0.0318
    }
  },
  "frames": [
    {
      "frame_index": 0,
      "filename": "frame_00.jpg",
      "status_code": 200,
      "status": "pass",
      "risk_level": "low",
      "explanation": "Adequate lighting supports stable AR tracking.",
      "triggered_rules": [],
      "recommendations": [],
      "metrics": {
        "illumination_score": 0.8124,
        "illumination_label": "adequate",
        "mean_brightness": 0.6012,
        "mean_luma": 153.3,
        "std_luma": 48.2,
        "uniformity": 0.8431,
        "pct_clipped_dark": 0.0021,
        "pct_clipped_bright": 0.0008
      }
    },
    {
      "frame_index": 1,
      "filename": "frame_01.jpg",
      "status_code": 200,
      "status": "fail",
      "risk_level": "high",
      "explanation": "Insufficient brightness degrades AR tracking.",
      "triggered_rules": ["Underexposed scene (too dark)"],
      "recommendations": ["Increase ambient lighting", "Avoid dark environments"],
      "metrics": {
        "illumination_score": 0.2341,
        "illumination_label": "underexposed",
        "mean_brightness": 0.2198,
        "mean_luma": 56.0,
        "std_luma": 31.4,
        "uniformity": 0.6812,
        "pct_clipped_dark": 0.1124,
        "pct_clipped_bright": 0.0001
      }
    }
  ]
}
```

**Error responses:**

| Code | Meaning |
|---|---|
| 404 | Batch not found |
| 409 | Diagnosis already in progress |
| 500 | Inference error |

---

### GET `/diagnose/batch/{batch_id}/status`

Returns the current processing status of a batch.

```bash
curl http://localhost:8000/diagnose/batch/batch_20260416_200002_74ee64/status
```

**Response:**

```json
{
  "batch_id": "batch_20260416_200002_74ee64",
  "status": "completed",
  "updated_at": "2026-04-16T20:00:15.123456"
}
```

**Status values:** `uploaded` → `processing` → `completed` / `failed`

---

### GET `/diagnose/batch/{batch_id}/result`

Retrieves the saved diagnosis result for a completed batch. Returns HTTP 202 if the diagnosis is not yet complete.

```bash
curl http://localhost:8000/diagnose/batch/batch_20260416_200002_74ee64/result
```

Response structure is identical to `POST /diagnose/batch/{batch_id}`.

---

## Usage Examples

### Python - Full batch flow

```python
import requests

API = "http://localhost:8000"
image_paths = ["frame_00.jpg", "frame_01.jpg", "frame_02.jpg"]

# Step 1: upload
files = [("files", open(p, "rb")) for p in image_paths]
upload = requests.post(f"{API}/upload/batch", files=files).json()
batch_id = upload["batch_id"]

# Step 2: diagnose
result = requests.post(f"{API}/diagnose/batch/{batch_id}").json()

print(f"Environment: {result['metadata']['environment']}")
print(f"SLM latency: {result['performance']['slm_per_diagnosis_s']:.3f}s/frame")
print(f"Target met: {result['performance']['target_met']}")
print(f"Summary: {result['summary']['explanation']}")

for frame in result["frames"]:
    print(f"  {frame['filename']}: {frame['status']} ({frame['metrics']['illumination_label']})")
```

### curl - Minimal example

```bash
# Upload
BATCH_ID=$(curl -s -X POST http://localhost:8000/upload/batch \
  -F "files=@frame_00.jpg" \
  | jq -r '.batch_id')

# Diagnose
curl -s -X POST http://localhost:8000/diagnose/batch/$BATCH_ID | jq '.summary.explanation'

# Check per-frame results
curl -s http://localhost:8000/diagnose/batch/$BATCH_ID/result \
  | jq '.frames[] | {file: .filename, status: .status, label: .metrics.illumination_label}'
```

---

## Output Validation

All SLM outputs pass through `OutputValidator` before being included in the response. If validation fails, the system falls back to a deterministic template explanation.

DialoGPT-small applies an additional model-specific post-processing step that rejects conversational, repetitive, or artifact-heavy outputs before the shared validator runs. This is necessary because DialoGPT is a conversational model not trained for diagnostic tasks.

---

## Configuration

Key settings in `app/config/thresholds.yaml`:

```yaml
models:
  default: qwen              # Model to load on startup
  device: cuda
  use_4bit: false            # Enable for Desktop Legion
  greedy_decoding: true      # Faster; disable for more varied outputs
  prompt_max_length: 512     # Use 256 for Jetson Nano
  warmup_on_startup: true    # Recommended: eliminates first-request spike

api:
  max_batch_size: 10
  max_image_size: 10485760   # 10 MB
  allowed_formats: [jpg, jpeg, png, bmp]
  upload_dir: data/uploads
  output_dir: outputs

pdi:
  illumination:
    clipped_bright_overexposed: 0.10
    clipped_dark_underexposed: 0.10
    mean_underexposed: 70
    mean_overexposed: 185
    good: 0.7
    min_acceptable: 0.5
```

The execution environment is detected automatically from environment variables, YAML config, hostname, or GPU name. It can be overridden explicitly:

```bash
export AR_ENVIRONMENT=jetson-orin
```