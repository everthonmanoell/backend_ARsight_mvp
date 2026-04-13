import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

# List all tests in past 30 minutes, sorted by time
legion_dir = Path('outputs/legion')
tests = sorted(
    legion_dir.glob('pipeline_test_*.json'),
    key=lambda p: p.stat().st_mtime,
    reverse=True
)

print("=" * 80)
print("PERFORMANCE TIMELINE - Last 10 tests")
print("=" * 80)

for i, test_file in enumerate(tests[:10]):
    with open(test_file) as f:
        data = json.load(f)
    
    ts = data['metadata']['timestamp']
    model = data['metadata']['model']
    slm_total = data['performance']['slm_total_s']
    slm_per = data['performance']['slm_per_diagnosis_s']
    
    # Extract year/month/day/hour/min/sec from ...T23:35:04...
    time_str = ts.split('T')[1]
    
    print(f"{i+1}. {test_file.name}: {slm_total:7.2f}s total, {slm_per:6.3f}s/diag | {model}")

print("\n" + "=" * 80)
print("ANALYSIS")
print("=" * 80)

# Find the fastest
fastest = tests[0]
with open(fastest) as f:
    data = json.load(f)
print(f"Fastest recent: {fastest.name} = {data['performance']['slm_total_s']:.2f}s")

# Find the baseline (6.265s)
for test_file in tests:
    with open(test_file) as f:
        data = json.load(f)
    if abs(data['performance']['slm_total_s'] - 6.265) < 0.1:
        print(f"Found baseline-like: {test_file.name} = {data['performance']['slm_total_s']:.2f}s")

print("\nTarget: ~6s")
print(f"Current fastest: {data['performance']['slm_total_s']:.2f}s")
print(f"Slowdown factor: {data['performance']['slm_total_s'] / 6.265:.1f}x")
