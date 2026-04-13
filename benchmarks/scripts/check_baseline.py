import json

# Check the fast baseline
with open('outputs/legion/pipeline_test_20260315_204720.json') as f:
    data = json.load(f)

print("=" * 80)
print("FAST BASELINE (6.265s) - Configuration & Samples")
print("=" * 80)
print(f"\nMetadata: {data['metadata']}")
print(f"Performance: {data['performance']}")

frames = data.get('frames', [])
print(f"\n\nSample explanations from frames (showing first 5):")
for i, frame in enumerate(frames[:5]):
    print(f"\n[Frame {i}] Status={frame.get('status')} | Label={frame.get('predicted_label')}")
    print(f"Explanation: {frame.get('explanation', 'N/A')}")

# Check summary
summary = data.get('summary', {})
print(f"\n\nSummary explanation:")
print(f"{summary.get('explanation', 'N/A')}")
