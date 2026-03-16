import json
from pathlib import Path

files = sorted(Path('outputs/legion').glob('*.json'), key=lambda x: x.stat().st_mtime)
latest = files[-1]

d = json.load(open(latest))  
perf = d['performance']
print(f"Latest test: {latest.name}")
print(f"Performance:")
print(f"  Total: {perf['total_s']:.2f}s")
print(f"  Per diagnosis: {perf['slm_per_diagnosis_s']:.2f}s")
print(f"\nSample outputs:")
for i, frame in enumerate(d['frames'][:3]):
    print(f"\nFrame {i} ({frame['expected_label']}): {frame['explanation'][:80]}")
