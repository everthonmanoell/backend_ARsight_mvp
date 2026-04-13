import json
from pathlib import Path
import os

legion_dir = Path("outputs/legion")
files = sorted(legion_dir.glob("*.json"), key=lambda x: x.stat().st_mtime, reverse=True)

if files:
    latest = files[0]
    try:
        data = json.load(open(latest))
        print(f"Latest test: {latest.name}")
        print(f"Duration: {data['performance']['total_s']:.2f}s")
        print(f"Per diagnosis: {data['performance']['slm_per_diagnosis_s']:.2f}s")
        print(f"Model: {data['metadata']['model']}")
        
        # Show last 5 tests for comparison
        print("\nLast 5 tests:")
        for f in files[:5]:
            d = json.load(open(f))
            print(f"  {f.name}: {d['performance']['total_s']:.2f}s")
    except Exception as e:
        print(f"Error: {e}")
