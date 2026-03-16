import json

d = json.load(open('outputs/legion/pipeline_test_20260315_235954.json'))
frames = d['frames']
print("SAMPLE MODEL OUTPUTS (first 5 frames)")
print("=" * 80)
for i, f in enumerate(frames[:5]):
    label = f['expected_label']
    explanation = f['explanation']
    sentence_count = explanation.count('.') + explanation.count('!') + explanation.count('?')
    print(f"\nFrame {i}: {label}")
    print(f"  Explanation: {explanation}")
    print(f"  Sentence count: {sentence_count}")
    print(f"  Char count: {len(explanation)}")

print("\n" + "=" * 80)
print("SUMMARY OUTPUT:")
print(f"Overall risk: {d['summary']['overall_risk']}")
print(f"Explanation: {d['summary']['explanation']}")
