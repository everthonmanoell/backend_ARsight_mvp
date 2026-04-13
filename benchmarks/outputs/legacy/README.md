# Legacy - Histórico de Benchmarks Antigos

Dados históricos de testes anteriores, mantidos para referência.

## 📂 Estrutura

```
legacy/
├── desktop-legion/
│   ├── batch1/
│   ├── batch2/
│   └── batch6/
├── jetson-nano/
│   ├── batch1/
│   ├── batch2/
│   └── batch6/
└── jetson-orin/
    ├── batch1/
    ├── batch2/
    └── batch6/
```

---

## 🗂️ O que tem em cada batch

```
batch1/
├── run_1.json
├── run_2.json
├── ...
├── run_5.json
└── summary.json  (agregado)
```

### Formato JSON (exemplo)

```json
{
  "run_id": 1,
  "timestamp": "2026-04-07T22:25:22",
  "timings": [
    {"image": "img1.jpg", "total_ms": 285},
    {"image": "img2.jpg", "total_ms": 292}
  ],
  "batch_total_s": 2.85,
  "mean_ms": 287.5,
  "throughput_imgs_per_sec": 3.49
}
```

---

## 🔍 Como Usar Dados Antigos

### Comparar Nano antigo vs. novo

```bash
# Ver dados antigos do Nano batch1
cat legacy/jetson-nano/batch1/summary.json

# Comparar com novo (em ../comparison/)
cat ../comparison/runs_raw.csv | grep "jetson-nano"
```

### Análise histórica

```bash
# Ver progression ao longo do tempo
cd legacy/jetson-nano/
for b in batch*/; do
  echo "=== $b ==="
  cat $b/summary.json | grep throughput
done
```

### Encontrar performance baseline

```bash
# Qual era a melhor performance no Nano?
for b in jetson-nano/batch*/; do
  echo "$b: $(cat $b/summary.json | grep mean_ms)"
done
```

---

## 📊 Quando Usar Legacy

### ✅ Recomendado verificar legacy quando:

1. **Quer ver tendência histórica**
   ```bash
   Nano batch1 performance em marzo vs. abril
   ```

2. **Precisa de baseline para comparação**
   ```bash
   "Isso é regressão? Vou checar o legacy"
   ```

3. **Investigar mudanças de código**
   ```bash
   "Quando é que performance caiu?"
   "Vou comparar com o commit antigo que tem dados em legacy"
   ```

4. **Documentar mudanças para TCC**
   ```bash
   "Demonstrar otimizações ao longo do tempo"
   ```

---

## 🗑️ Limpeza

### Se legacy ficar muito grande

```bash
# Comprimir antigos
tar -czf legacy_archive_2026-01.tar.gz desktop-legion/

# Remover pasta original
rm -rf desktop-legion/

# Mover arquivo para backups
mv legacy_archive_2026-01.tar.gz ~/backups/
```

### Se quiser remover tudo

```bash
rm -rf legacy/*
```

---

## 📝 Adicionar Novos Dados

Se quer manter histórico quando roda novo teste:

```bash
# Fazer backup antes
mkdir legacy/old_run_$(date +%Y%m%d_%H%M%S)
mv ../comparison/*.csv legacy/old_run_*/

# Depois roda novo teste
cd ..
python scripts/generate_comparison_report.py

# Novos dados em comparison/, antigos em legacy/
```

---

## 📍 Referência

Ver estrutura completa em: `../README.md`

---

**Última atualização:** 2026-04-13
