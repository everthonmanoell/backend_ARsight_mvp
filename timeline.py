import json
import os
from pathlib import Path

# Check baseline
d = json.load(open('outputs/legion/pipeline_test_20260315_204720.json'))
print(f"BASELINE 6.3s: {d['metadata']['timestamp']}")
print(f"  Total: {d['performance']['total_s']}s")
print()
# Check fastest recent
d = json.load(open('outputs/legion/pipeline_test_20260315_225714.json'))
print(f"FASTEST RECENT 17.6s: {d['metadata']['timestamp']}")
print(f"  Total: {d['performance']['total_s']}s")
print()

# Check other intermediate tests
test_files = {
    'pipeline_test_20260315_204720.json': '6.3s baseline',
    'pipeline_test_20260315_225238.json': 'First recent',
    'pipeline_test_20260315_225356.json': 'Second recent',
    'pipeline_test_20260315_225714.json': 'Fastest recent (17.6s)',
    'pipeline_test_20260315_230401.json': 'After fastest',
}

print("TIMELINE:")
for filename, desc in test_files.items():
    path = f'outputs/legion/{filename}'
    if os.path.exists(path):
        d = json.load(open(path))
        ts = d['metadata']['timestamp']
        total = d['performance']['total_s']
        print(f"{ts} | {total:.2f}s | {desc}")
