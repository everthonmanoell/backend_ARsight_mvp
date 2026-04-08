# Benchmark de Performance - Desktop Legion vs Jetson Nano vs Jetson Orin

Gerado em: 2026-04-07T22:25:22

## Resumo por ambiente/modelo/batch

| environment | model | batch | runs | total_s_mean | slm_per_diag_mean | pdi_per_image_ms_mean | accuracy_mean | target_met_rate |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| desktop-legion | phi | batch1 | 5 | 6.911 | 0.672 | 19.200 | 100.000 | 100.0% |
| desktop-legion | phi | batch2 | 5 | 9.421 | 0.924 | 18.180 | 100.000 | 40.0% |
| desktop-legion | phi | batch3 | 5 | 7.512 | 0.732 | 19.100 | 100.000 | 100.0% |
| desktop-legion | phi | batch4 | 5 | 9.426 | 0.924 | 18.280 | 100.000 | 80.0% |
| desktop-legion | phi | batch5 | 5 | 7.261 | 0.709 | 17.300 | 100.000 | 100.0% |
| desktop-legion | phi | batch6 | 5 | 6.767 | 0.661 | 15.160 | 100.000 | 100.0% |
| desktop-legion | qwen | batch1 | 5 | 3.542 | 0.337 | 16.540 | 100.000 | 100.0% |
| desktop-legion | qwen | batch2 | 5 | 3.527 | 0.339 | 13.160 | 100.000 | 100.0% |
| desktop-legion | qwen | batch3 | 5 | 3.834 | 0.369 | 14.300 | 100.000 | 100.0% |
| desktop-legion | qwen | batch4 | 5 | 4.163 | 0.404 | 12.980 | 100.000 | 100.0% |
| desktop-legion | qwen | batch5 | 5 | 3.817 | 0.368 | 13.260 | 100.000 | 100.0% |
| desktop-legion | qwen | batch6 | 5 | 4.224 | 0.409 | 13.780 | 100.000 | 100.0% |
| jetson-nano | qwen | batch1 | 14 | 148.736 | 14.774 | 99.221 | 100.000 | 0.0% |
| jetson-nano | qwen | batch2 | 8 | 159.683 | 15.858 | 110.725 | 100.000 | 0.0% |
| jetson-nano | qwen | batch3 | 14 | 155.574 | 15.413 | 144.650 | 100.000 | 0.0% |
| jetson-nano | qwen | batch4 | 15 | 154.509 | 15.310 | 140.740 | 100.000 | 0.0% |
| jetson-nano | qwen | batch5 | 11 | 164.204 | 16.229 | 191.682 | 100.000 | 0.0% |
| jetson-nano | qwen | batch6 | 13 | 153.291 | 15.114 | 214.962 | 100.000 | 0.0% |
| jetson-orin | phi | batch1 | 6 | 6.443 | 0.627 | 17.067 | 100.000 | 100.0% |
| jetson-orin | phi | batch2 | 6 | 7.859 | 0.768 | 17.533 | 100.000 | 100.0% |
| jetson-orin | phi | batch3 | 6 | 7.265 | 0.708 | 18.300 | 100.000 | 100.0% |
| jetson-orin | phi | batch4 | 6 | 6.088 | 0.591 | 17.483 | 100.000 | 100.0% |
| jetson-orin | phi | batch5 | 6 | 7.478 | 0.731 | 17.050 | 100.000 | 100.0% |
| jetson-orin | phi | batch6 | 6 | 6.643 | 0.647 | 17.367 | 100.000 | 100.0% |
| jetson-orin | qwen | batch1 | 6 | 3.594 | 0.343 | 16.800 | 100.000 | 100.0% |
| jetson-orin | qwen | batch2 | 6 | 3.977 | 0.379 | 18.350 | 100.000 | 100.0% |
| jetson-orin | qwen | batch3 | 6 | 3.963 | 0.377 | 19.267 | 100.000 | 100.0% |
| jetson-orin | qwen | batch4 | 6 | 3.750 | 0.357 | 18.200 | 100.000 | 100.0% |
| jetson-orin | qwen | batch5 | 6 | 3.735 | 0.356 | 17.900 | 100.000 | 100.0% |
| jetson-orin | qwen | batch6 | 6 | 4.430 | 0.424 | 18.583 | 100.000 | 100.0% |

## Speedup vs Desktop Legion

|model|batch|jetson-orin_speedup_vs_legion_slm_x|jetson-orin_speedup_vs_legion_total_x|
|---|---|---|---|
|phi|batch1|1.071|1.073|
|phi|batch2|1.203|1.199|
|phi|batch3|1.034|1.034|
|phi|batch4|1.563|1.548|
|phi|batch5|0.970|0.971|
|phi|batch6|1.023|1.019|
|qwen|batch1|0.985|0.986|
|qwen|batch2|0.894|0.887|
|qwen|batch3|0.979|0.967|
|qwen|batch4|1.131|1.110|
|qwen|batch5|1.036|1.022|
|qwen|batch6|0.963|0.953|
