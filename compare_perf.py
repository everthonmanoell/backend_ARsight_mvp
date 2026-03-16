import json

tests = {
    'baseline_6.39s': 'outputs/legion/pipeline_test_20260315_204720.json',
    'current_58.94s': 'outputs/legion/pipeline_test_20260315_235954.json',
}

print("TIME BREAKDOWN COMPARISON")
print("=" * 80)
for label, filepath in tests.items():
    try:
        d = json.load(open(filepath))
        pdi = d['performance']['pdi_total_ms'] / 1000
        slm = d['performance']['slm_total_s']
        total = d['performance']['total_s']
        slm_per_diag = d['performance']['slm_per_diagnosis_s']
        
        print(f"\n{label}:")
        print(f"  PDI (images):        {pdi:6.2f}s ({pdi/total*100:5.1f}%)")
        print(f"  SLM (inference):     {slm:6.2f}s ({slm/total*100:5.1f}%)")
        print(f"  SLM per diagnosis:   {slm_per_diag:6.2f}s")
        print(f"  Total:               {total:6.2f}s")
    except Exception as e:
        print(f"  Error: {e}")
