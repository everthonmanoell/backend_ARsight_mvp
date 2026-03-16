import json
import os
from pathlib import Path

legion_dir = Path("outputs/legion")
files = sorted(legion_dir.glob("*.json"), key=lambda x: x.stat().st_mtime, reverse=True)[:10]

print("RECENT TESTS WITH CONFIGS")
print("=" * 80)
for f in files:
    try:
        data = json.load(open(f))
        total_s = data["performance"]["total_s"]
        model = data["metadata"]["model"]
        qwen_tokens = data["config"]["models"]["qwen"]["max_tokens"]
        qwen_temp = data["config"]["models"]["qwen"]["temperature"]
        timestamp = f.name.split("_")[2:4]
        print(f"{f.name}")
        print(f"  Time: {total_s:.2f}s | Model: {model} | Qwen tokens: {qwen_tokens} | Temp: {qwen_temp}")
        print()
    except Exception as e:
        print(f"Error reading {f.name}: {e}")
