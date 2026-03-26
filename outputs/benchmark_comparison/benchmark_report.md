# Benchmark Jetson vs Legion

Gerado em: 2026-03-25T22:59:39

## Resumo por ambiente/modelo/batch

| environment | model | batch | runs | total_s_mean | slm_per_diag_mean | pdi_per_image_ms_mean | accuracy_mean | target_met_rate |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| jetson | qwen | batch1 | 14 | 148.736 | 14.774 | 99.221 | 100.000 | 0.0% |
| jetson | qwen | batch2 | 8 | 159.683 | 15.858 | 110.725 | 100.000 | 0.0% |
| jetson | qwen | batch3 | 14 | 155.574 | 15.413 | 144.650 | 100.000 | 0.0% |
| jetson | qwen | batch4 | 15 | 154.509 | 15.310 | 140.740 | 100.000 | 0.0% |
| jetson | qwen | batch5 | 11 | 164.204 | 16.229 | 191.682 | 100.000 | 0.0% |
| jetson | qwen | batch6 | 13 | 153.291 | 15.114 | 214.962 | 100.000 | 0.0% |
| legion | phi | batch1 | 5 | 6.911 | 0.672 | 19.200 | 100.000 | 100.0% |
| legion | phi | batch2 | 5 | 9.421 | 0.924 | 18.180 | 100.000 | 40.0% |
| legion | phi | batch3 | 5 | 7.512 | 0.732 | 19.100 | 100.000 | 100.0% |
| legion | phi | batch4 | 5 | 9.426 | 0.924 | 18.280 | 100.000 | 80.0% |
| legion | phi | batch5 | 5 | 7.261 | 0.709 | 17.300 | 100.000 | 100.0% |
| legion | phi | batch6 | 5 | 6.767 | 0.661 | 15.160 | 100.000 | 100.0% |
| legion | qwen | batch1 | 5 | 3.542 | 0.337 | 16.540 | 100.000 | 100.0% |
| legion | qwen | batch2 | 5 | 3.527 | 0.339 | 13.160 | 100.000 | 100.0% |
| legion | qwen | batch3 | 5 | 3.834 | 0.369 | 14.300 | 100.000 | 100.0% |
| legion | qwen | batch4 | 5 | 4.163 | 0.404 | 12.980 | 100.000 | 100.0% |
| legion | qwen | batch5 | 5 | 3.817 | 0.368 | 13.260 | 100.000 | 100.0% |
| legion | qwen | batch6 | 5 | 4.224 | 0.409 | 13.780 | 100.000 | 100.0% |

## Speedup (Legion vs Jetson)

| model | batch | legion_speedup_total_x | legion_speedup_slm_x |
|---|---:|---:|---:|
| qwen | batch1 | 41.992 | 43.789 |
| qwen | batch2 | 45.272 | 46.750 |
| qwen | batch3 | 40.582 | 41.746 |
| qwen | batch4 | 37.117 | 37.934 |
| qwen | batch5 | 43.019 | 44.052 |
| qwen | batch6 | 36.294 | 36.990 |
