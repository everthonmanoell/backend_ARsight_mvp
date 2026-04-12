# Testing DialoGPT-small on Jetson Nano with Poetry

## Quick Start

### Option 1: Remote test from Desktop (SSH)
```bash
cd ~/TCC/backend_tcc_mvp
./run_dialogpt_test_poetry.sh
```

This script will:
1. ✅ SSH to Jetson Nano
2. ✅ Set up Poetry environment
3. ✅ Run the test suite
4. ✅ Display results with VRAM usage

### Option 2: Manual test on Jetson Nano
```bash
# 1. SSH to Jetson
ssh jetson

# 2. Navigate to project
cd ~/tcc/backend_tcc_mvp

# 3. Run with Poetry
poetry run python test_dialogpt_nano.py

# Or with pip (if Poetry not available)
python3 test_dialogpt_nano.py
```

### Option 3: Test inside Docker container
```bash
# From Jetson Nano
ssh jetson

# Enter container
docker exec -it ar-diagnostic-mvp-nano bash

# Run test
python test_dialogpt_nano.py
```

## What the test does

The `test_dialogpt_nano.py` script validates:

1. **Model Loading** ✅
   - Loads DialoGPT-small from HuggingFace
   - Places on CUDA (or CPU fallback)
   - Verifies YAML config loading

2. **Single Inference** ✅
   - Generates a test prompt
   - Runs single inference
   - Measures latency

3. **Batch Inference** ✅
   - Processes 3 prompts in parallel
   - Measures batch throughput
   - Compares to single inference

4. **Summary Prompt** ✅
   - Tests batch summary generation
   - Validates aggregation logic

5. **VRAM Usage** ✅
   - Reports allocated/reserved VRAM
   - Checks if usage is < 50%
   - Essential for Jetson Nano stability

## Expected Results

For Jetson Nano with 4GB VRAM:

```
TEST 1: Model Loading
✅ Model loaded successfully on device: cuda
   Model name: microsoft/DialoGPT-small
   Max tokens: 40
   Greedy decoding: True

TEST 2: Single Inference
✅ Single inference completed in 0.45s
   Response: Scene lighting analysis confirmed...

TEST 3: Batch Inference (3 prompts)
✅ Batch inference completed in 1.10s
   Average time per prompt: 0.37s

TEST 4: Summary Prompt
✅ Summary inference completed in 0.42s

TEST 5: VRAM Usage
✅ VRAM Status:
   Allocated: 0.38 GB
   Reserved:  0.85 GB
   Total:     3.80 GB
   Free:      2.95 GB
   ✅ VRAM usage is healthy (< 50%)
```

## Benchmarks to Target

| Metric | Target | Note |
|--------|--------|------|
| **Model Loading** | < 5s | First time is slow |
| **Single Inference** | 0.3-0.5s | 40 tokens max |
| **Batch (3 prompts)** | 1.0-1.5s | ~0.35s/prompt avg |
| **VRAM Allocated** | < 1.0 GB | Leaves room for input |
| **VRAM Reserved** | < 2.0 GB | Safety margin for Jetson |

## Troubleshooting

### ❌ "Model not found" or Download timeout
```bash
# Pre-cache model on desktop
huggingface-cli download microsoft/DialoGPT-small

# Or on Jetson:
ssh jetson
docker exec ar-diagnostic-mvp-nano python3 -c "from transformers import AutoModel; AutoModel.from_pretrained('microsoft/DialoGPT-small')"
```

### ❌ "Out of memory" or VRAM > 50%
- Reduce `prompt_max_length` in `thresholds.yaml` to 128
- Enable batch processing (more efficient than single inference)
- Check other processes with `nvidia-smi` on Jetson

### ❌ Poetry not found
The script automatically falls back to pip:
```bash
pip3 install -r requirements-jetson-nano.txt
python3 test_dialogpt_nano.py
```

### ⚠️ Slow first inference (TTFT)
- Normal: model warms up on first call
- Subsequent calls will be faster
- Production: Use warmup_on_startup in config

## Next Steps

After successful test:

1. **Deploy to container**
   ```bash
   git push
   # On Jetson:
   cd ~/tcc/backend_tcc_mvp
   docker build -f docker/Dockerfile.jetson-nano -t ar-diagnostic-mvp:nano .
   docker run -d --gpus all -p 8000:8000 \
     -v $(pwd)/data:/app/data \
     -v $(pwd)/models/cache:/app/models/cache \
     ar-diagnostic-mvp:nano
   ```

2. **Test API**
   ```bash
   curl -s http://localhost:8000/health | jq
   ```

3. **Run end-to-end batch test**
   ```bash
   curl -X POST http://localhost:8000/diagnose/batch \
     -F "images=@test_image.jpg" \
     -F "images=@test_image2.jpg"
   ```

## Configuration Reference

Edit `app/config/thresholds.yaml` to adjust:

```yaml
models:
  default: dialogpt-small           # ✅ Set to dialogpt-small for Nano
  device: cuda                       # ✅ CUDA (Jetson has GPU)
  greedy_decoding: true              # ✅ Speed preference
  prompt_max_length: 256             # Adjust if VRAM issues
  
  dialogpt-small:
    max_tokens: 40                   # Response length
    summary_tokens: 60               # Batch summary length
    temperature: 0.3                 # (ignored with greedy)
```

---

**For questions or issues:** Check logs with `docker logs ar-diagnostic-mvp-nano | tail -50`
