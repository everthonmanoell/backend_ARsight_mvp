# Benchmarking Guide

Guia completo para executar benchmarks, organizar resultados e gerar gráficos para TCC.

## 📊 Estrutura de Benchmarking Proposta

### Matriz de Testes Recomendada

```
┌─────────────────────────────────────────────────────────┐
│                 MODELO PRIMÁRIO (RECOMENDADO)            │
├─────────────────────────────────────────────────────────┤
│ Jetson Nano      → DialoGPT-small    ✅ Validado 3.4s   │
│ Jetson Orin      → Qwen 2.5-0.5B     ✅ Validado 3.3s   │
│ Desktop RTX      → Phi-3-mini        ✅ Validado 3.2s   │
├─────────────────────────────────────────────────────────┤
│              MODELOS ALTERNATIVOS (OPCIONAL)            │
├─────────────────────────────────────────────────────────┤
│ Jetson Nano      → Qwen (futuro)     ⏳ Teste opcional   │
│ Jetson Orin      → Phi-3 (futuro)    ⏳ Teste opcional   │
│ Desktop RTX      → Qwen (futuro)     ⏳ Teste opcional   │
├─────────────────────────────────────────────────────────┤
│        COMPARAÇÃO CROSS-MODELO (VISÃO GERAL)           │
├─────────────────────────────────────────────────────────┤
│ DialoGPT x3 envs (futuro)    → Gráficos comparativos   │
│ Qwen x3 envs (futuro)        → Gráficos comparativos   │
│ Phi x3 envs (futuro)         → Gráficos comparativos   │
└─────────────────────────────────────────────────────────┘
```

### Estrutura de Diretórios

```
outputs/
├── benchmarks/                           # NOVO - Organização por modelo prim.
│   ├── dialogpt-small/
│   │   ├── jetson-nano/                  # Modelo primário em Nano
│   │   │   ├── batch1/
│   │   │   │   ├── run_1.json
│   │   │   │   ├── run_2.json
│   │   │   │   └── ...
│   │   │   ├── batch2/
│   │   │   └── ...
│   │   ├── jetson-orin/ (futuro)         # Testes alternativos
│   │   ├── desktop-rtx/ (futuro)
│   │   └── reports/
│   │       ├── summary.csv
│   │       ├── summary.md
│   │       └── plots/
│   │           ├── latency_per_batch.png
│   │           ├── throughput_comparison.png
│   │           └── ...
│   │
│   ├── qwen/
│   │   ├── jetson-orin/                  # Modelo primário em Orin
│   │   ├── desktop-rtx/ (futuro)
│   │   ├── jetson-nano/ (futuro)
│   │   └── reports/
│   │
│   ├── phi/
│   │   ├── desktop-rtx/                  # Modelo primário em RTX
│   │   ├── jetson-orin/ (futuro)
│   │   ├── jetson-nano/ (futuro)
│   │   └── reports/
│   │
│   └── cross_model_comparison/           # Visão geral
│       ├── all_models_latency.png
│       ├── recommended_vs_alternatives.md
│       └── ...
│
├── jetson-nano/          # LEGADO - Manter para compatibilidade
├── jetson-orin/          # LEGADO
├── desktop-legion/       # LEGADO
└── benchmark_comparison/ # LEGADO
```

### Métricas Capturadas

Por cada batch de teste, capturamos:

```json
{
  "environment": "jetson-nano",
  "model": "dialogpt-small",
  "batch_id": "batch1",
  "run_id": 1,
  "timestamp": "2026-04-13T12:05:30",
  
  "timing": {
    "pdi_per_image_ms": 12.5,
    "llm_per_diag_ms": 280.3,
    "total_per_image_ms": 292.8,
    "batch_total_s": 2.93
  },
  
  "performance": {
    "images_per_second": 3.42,
    "diagrams_per_second": 3.57,
    "target_met": true,
    "target_threshold_ms": 300
  },
  
  "quality": {
    "validation_passed": 10,  # Quantos resolvidos no LLM
    "fallback_used": 0,        # Quantos usaram template fallback
    "accuracy": 100.0,         # % hits
    "validation_rate": 100.0   # % que passou validação
  },
  
  "system": {
    "gpu_name": "Tegra X1",
    "gpu_memory_gb": 4,
    "torch_cuda_available": true,
    "pytorch_version": "1.10.0"
  }
}
```

---

## 🚀 Como Executar Testes

### Passo 1: Setup Inicial

```bash
cd ~/TCC/backend_tcc_mvp

# Criar estrutura de diretórios
mkdir -p outputs/benchmarks/{dialogpt-small,qwen,phi}/{jetson-nano,jetson-orin,desktop-rtx}/reports/{plots}

# Verificar
ls -la outputs/benchmarks/
```

### Passo 2: Testes Primários (HOJE)

#### 2.1 Jetson Nano - DialoGPT (Modo Produção)

```bash
# SSH into Nano
ssh jetson

# Executar teste (10 imagens x 5 runs)
python test_dialogpt_nano.py \
  --batch-id batch1 \
  --num-runs 5 \
  --images 10 \
  --output outputs/benchmarks/dialogpt-small/jetson-nano/batch1/

# Repetir para outros batches
for batch in batch1 batch2 batch3; do
  python test_dialogpt_nano.py \
    --batch-id $batch \
    --num-runs 5 \
    --output outputs/benchmarks/dialogpt-small/jetson-nano/$batch/
done

# Gerar relatório deste modelo/env
python generate_benchmark_report.py \
  --model dialogpt-small \
  --environment jetson-nano \
  --input-dir outputs/benchmarks/dialogpt-small/jetson-nano/ \
  --output-dir outputs/benchmarks/dialogpt-small/jetson-nano/reports/
```

#### 2.2 Jetson Orin - Qwen (Modo Produção)

```bash
# SSH into Orin
ssh farmaciaback    # ou outro hostname

# Executar testes
for batch in batch1 batch2 batch3; do
  python test_qwen_orin.py \
    --batch-id $batch \
    --num-runs 5 \
    --output outputs/benchmarks/qwen/jetson-orin/$batch/
done

# Gerar relatório
python generate_benchmark_report.py \
  --model qwen \
  --environment jetson-orin \
  --input-dir outputs/benchmarks/qwen/jetson-orin/ \
  --output-dir outputs/benchmarks/qwen/jetson-orin/reports/
```

#### 2.3 Desktop RTX - Phi-3 (Modo Produção)

```bash
# Windows PowerShell ou Linux/Mac
cd backend_tcc_mvp

# Executar testes
for batch in batch1 batch2 batch3; do
  python test_phi_desktop.py `
    --batch-id $batch `
    --num-runs 5 `
    --output ./outputs/benchmarks/phi/desktop-rtx/$batch/
}

# Gerar relatório
python generate_benchmark_report.py `
  --model phi `
  --environment desktop-rtx `
  --input-dir ./outputs/benchmarks/phi/desktop-rtx/ `
  --output-dir ./outputs/benchmarks/phi/desktop-rtx/reports/
```

### Passo 3: Gerar Relatório Consolidado

```bash
# Depois que os 3 primários estão prontos:
python generate_consolidated_benchmark_report.py \
  --models-dir outputs/benchmarks/ \
  --output outputs/benchmarks/cross_model_comparison/

# Output:
# - all_models_latency_comparison.png
# - speedup_ratio_chart.png
# - recommended_vs_alternatives.md
# - detailed_summary.csv
```

### Passo 4: Testes Alternativos (FUTURO)

Uma vez que os 3 primários estão validados, opcionalmente testar alternativas:

```bash
# Jetson Orin - Phi-3
for batch in batch1 batch2 batch3; do
  python test_phi_orin.py \
    --batch-id $batch \
    --num-runs 5 \
    --output outputs/benchmarks/phi/jetson-orin/$batch/
done

# Desktop RTX - Qwen
for batch in batch1 batch2 batch3; do
  python test_qwen_desktop.py \
    --batch-id $batch \
    --num-runs 5 \
    --output outputs/benchmarks/qwen/desktop-rtx/$batch/
done
```

---

## 📈 Gráficos para TCC

### Recomendados (Primários)

Estes gráficos devem estar no relatório final:

1. **Latency Comparison** (todos os 3 modelos primários)
   ```
   DialoGPT-Nano vs Qwen-Orin vs Phi-RTX
   Y: Latência (ms)
   X: Batch number
   ```

2. **Throughput (Diagrams/sec)**
   ```
   Qwen-Orin vs Phi-RTX vs DialoGPT-Nano
   Y: Imagens/segundo
   X: Batch
   Linha vermelha: Target 3.3 imgs/sec
   ```

3. **Validation Rate (% passou 8-tier)**
   ```
   DialoGPT-Nano: 100%
   Qwen-Orin: 100%
   Phi-RTX: 100%
   ```

4. **Accuracy (Correct diagnoses / total)**
   ```
   Todos: 100%
   ```

### Opcionais (Se testes alternativos)

5. **Phi em todos os ambientes**
   - Nano: ✗ (sem VRAM)
   - Orin: ✓ (teste futuro)
   - RTX: ✓ (primário)

6. **Qwen em todos os ambientes**
   - Nano: ✓ (teste futuro)
   - Orin: ✓ (primário)
   - RTX: ✓ (teste futuro)

7. **DialoGPT em todos os ambientes**
   - Nano: ✓ (primário)
   - Orin: ✓ (teste futuro)
   - RTX: ✓ (teste futuro)

---

## 📝 Estrutura de Relatório para TCC

### Executivo

```markdown
## Executive Summary

- Jetson Nano: DialoGPT-small @ 292ms (3.42 imgs/sec) ✅
- Jetson Orin: Qwen 2.5-0.5B @ 320ms (3.12 imgs/sec) ✅
- Desktop RTX: Phi-3-mini @ 315ms (3.17 imgs/sec) ✅

Todos os ambientes atendem ao target de <300ms por diagnóstico.
```

### Seção 1: Recomendação Primária

```markdown
## 1. Configuração Recomendada por Ambiente

### 1.1 Jetson Nano
- Modelo: DialoGPT-small (117M)
- Performance: 292ms / imagem
- Métricas: [tabela com dados]
- Gráfico: [latency_nano.png]

### 1.2 Jetson Orin
- Modelo: Qwen 2.5-0.5B (494M)
- Performance: 320ms / imagem
- Métricas: [tabela com dados]
- Gráfico: [latency_orin.png]

### 1.3 Desktop RTX
- Modelo: Phi-3-mini (3.8B)
- Performance: 315ms / imagem
- Métricas: [tabela com dados]
- Gráfico: [latency_rtx.png]
```

### Seção 2: Análise Comparativa

```markdown
## 2. Análise Comparativa entre Ambientes

### 2.1 Throughput
[Gráfico de barras mostrando imgs/sec para cada]

### 2.2 Scaling Efficiency
[Speedup vs CPU-only baseline]

### 2.3 Power Efficiency
[Se disponível: Watts per diagnosis]
```

### Seção 3: Modelos Alternativos (se testados)

```markdown
## 3. Análise de Modelos Alternativos (Opcional)

### 3.1 Phi-3 em Jetson Orin
- Performance: 850ms (vs Qwen: 320ms)
- Qualidade: Similar (ambos LLMs boas)
- Conclusão: Qwen preferido para Orin

### 3.2 Qwen em Desktop RTX
- Performance: 150ms (vs Phi: 315ms)
- Qualidade: Similar
- Conclusão: Phi oferece melhor raciocínio, mas Qwen mais rápido
```

---

## 🔧 Scripts Necessários

### 1. `test_dialogue_model.py` (Genérico)

```python
"""
Executor genérico de testes para qualquer modelo/ambiente
"""
import argparse
import json
import time
from pathlib import Path
from datetime import datetime
from PIL import Image
from app.pipeline.illumination_pipeline import IlluminationPipeline

def run_benchmark(
    model_type: str,
    batch_id: str,
    num_runs: int,
    images_dir: str,
    output_dir: str,
    target_threshold_ms: int = 300
):
    """Executa benchmark e salva resultados"""
    
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    pipeline = IlluminationPipeline(model_type=model_type, device="cuda")
    
    # Carregar imagens
    images = list(Path(images_dir).glob("*.jpg"))[:10]
    
    results = []
    
    for run_num in range(1, num_runs + 1):
        run_start = time.time()
        run_results = {
            "run_id": run_num,
            "timestamp": datetime.now().isoformat(),
            "timings": [],
            "quality": {"passed": 0, "failed": 0}
        }
        
        for img_path in images:
            img_start = time.time()
            image = Image.open(img_path)
            
            # Pipeline completo
            metrics = pipeline.extract_metrics_batch([image])[0]
            diagnosis, summary = pipeline.diagnose_from_metrics_batch_with_summary([metrics])
            
            elapsed_ms = (time.time() - img_start) * 1000
            
            run_results["timings"].append({
                "image": img_path.name,
                "total_ms": elapsed_ms,
                "passed_target": elapsed_ms < target_threshold_ms
            })
            
            if diagnosis[0]:  # Se LLM não foi rejeitado
                run_results["quality"]["passed"] += 1
            else:
                run_results["quality"]["failed"] += 1
        
        run_results["batch_total_s"] = time.time() - run_start
        run_results["mean_ms"] = sum(t["total_ms"] for t in run_results["timings"]) / len(run_results["timings"])
        run_results["throughput_imgs_per_sec"] = len(images) / run_results["batch_total_s"]
        
        results.append(run_results)
        
        # Salvar resultado individual
        with open(output_dir / f"run_{run_num}.json", "w") as f:
            json.dump(run_results, f, indent=2)
        
        print(f"  Run {run_num}/{num_runs}: {run_results['mean_ms']:.1f}ms/img, "
              f"{run_results['throughput_imgs_per_sec']:.2f} imgs/sec")
    
    # Salvar resumo do batch
    with open(output_dir / "summary.json", "w") as f:
        json.dump({
            "batch_id": batch_id,
            "model": model_type,
            "num_runs": num_runs,
            "mean_latency_ms": sum(r["mean_ms"] for r in results) / len(results),
            "mean_throughput": sum(r["throughput_imgs_per_sec"] for r in results) / len(results),
            "total_quality_rate": sum(r["quality"]["passed"] for r in results) / 
                                  (sum(r["quality"]["passed"] + r["quality"]["failed"] for r in results))
        }, f, indent=2)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", required=True, choices=["dialogpt-small", "qwen", "phi"])
    parser.add_argument("--batch-id", required=True)
    parser.add_argument("--num-runs", type=int, default=5)
    parser.add_argument("--images-dir", default="data/illumination")
    parser.add_argument("--output-dir", required=True)
    
    args = parser.parse_args()
    
    run_benchmark(
        model_type=args.model,
        batch_id=args.batch_id,
        num_runs=args.num_runs,
        images_dir=args.images_dir,
        output_dir=args.output_dir
    )
```

### 2. `generate_benchmark_report.py`

Gera relatórios coloridos e gráficos por modelo/env.

### 3. `generate_consolidated_report.py`

Gera comparação cross-model/env consolidada.

---

## 📚 Checklist para TCC

- [ ] Definir 3 batches de testes (10 imagens cada)
- [ ] Executar 5 runs por batch em Nano (DialoGPT)
- [ ] Executar 5 runs por batch em Orin (Qwen)
- [ ] Executar 5 runs por batch em Desktop (Phi)
- [ ] Gerar relatórios individuais (3 arquivos markdown + gráficos)
- [ ] Gerar relatório consolidado
- [ ] Incluir gráficos no TCC:
  - [ ] Latency comparison
  - [ ] Throughput comparison
  - [ ] Validation rate
  - [ ] Accuracy
- [ ] Descrever recomendações
- [ ] (Opcionalmente) Testar modelos alternativos se tempo permitir

---

## 🎯 Quick Commands

```bash
# Tudo em um comando (depois que preparado)
bash run_full_benchmark.sh

# Apenas gerar relatórios (se dados já existem)
python generate_consolidated_benchmark_report.py \
  --models-dir outputs/benchmarks/ \
  --output outputs/benchmarks/TCC_final/
```

---

## 📖 Referências

- [Benchmark Report Template](../outputs/benchmark_comparison/benchmark_report.md)
- [Raw Data Format](../outputs/benchmark_comparison/runs_raw.csv)
- [API_GUIDE.md - Performance Section](API_GUIDE.md#performance)
