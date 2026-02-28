# 🔥 API Warm-up e torch.compile() - Guia Completo

## 📋 O que foi implementado?

### ✅ Warm-up Automático no Startup

Agora quando a API iniciar, **ANTES** de aceitar requisições:

1. ✅ Carrega os pesos do modelo
2. ✅ Faz uma inferência com imagem dummy
3. ✅ Se `enable_compile=true`: compila o modelo (2-5min)
4. ✅ Só então aceita requisições

**Resultado:** Primeira requisição **NÃO** fica lenta! Tudo já está pronto.

---

## ⚙️ Configuração

### Arquivo: `app/config/thresholds.yaml`

```yaml
models:
  default: qwen
  device: cuda
  use_4bit: true
  
  # 🆕 NOVAS OPÇÕES:
  enable_compile: false      # torch.compile() para +10-30% velocidade
  warmup_on_startup: true    # Warm-up automático (RECOMENDADO)
```

---

## 🚀 Cenários de Uso

### 1. DESENVOLVIMENTO (padrão atual)
```yaml
enable_compile: false
warmup_on_startup: true
```

**Startup:** ~10-15s (carrega pesos, 1 inferência dummy)  
**Performance:** 0.96s/img com TRUE BATCH  
**Vantagens:**
- ✅ Startup rápido
- ✅ Sem delay na primeira requisição
- ✅ Ideal para dev/debug

---

### 2. PRODUÇÃO SEM COMPILE (sem torch.compile)
```yaml
enable_compile: false
warmup_on_startup: true
```

**Mesmo que desenvolvimento!**

---

### 3. PRODUÇÃO COM COMPILE ⚡ (máxima performance)
```yaml
enable_compile: true
warmup_on_startup: true
```

**Startup:** ~3-7min (carrega pesos + compila modelo)  
**Performance:** ~0.70s/img com TRUE BATCH (+27% mais rápido!)  
**Vantagens:**
- ✅ MÁXIMA velocidade de inferência
- ✅ Sem delay na primeira requisição
- ✅ Ideal para produção de longa duração

**⚠️ Trade-off:**
- ❌ Startup MUITO mais lento (3-7min vs 15s)
- ⚠️ Requer PyTorch 2.0+

---

### 4. SEM WARM-UP (não recomendado)
```yaml
enable_compile: false
warmup_on_startup: false
```

**Startup:** ~1s (quase instantâneo)  
**Performance:** Primeira requisição leva ~10-15s (carregando pesos)  
**Desvantagens:**
- ❌ Primeira requisição MUITO lenta
- ❌ Má experiência para usuário

---

## 📊 Comparação de Performance

| Configuração | Startup | 1ª Requisição | Requisições Seguintes |
|--------------|---------|---------------|----------------------|
| **Sem warm-up** | ~1s | 🐌 10-15s | ⚡ 0.96s/img |
| **Com warm-up** | ~15s | ⚡ 0.96s/img | ⚡ 0.96s/img |
| **+ compile** | 🐌 3-7min | ⚡ 0.70s/img | ⚡ 0.70s/img |

---

## 🧪 Como Testar

### 1. Testar Warm-up Padrão (sem compile)

```bash
# thresholds.yaml:
# enable_compile: false
# warmup_on_startup: true

uvicorn app.api.main:app --reload
```

**Você verá:**
```
Loading pipeline (model: qwen, 4-bit: True, device: cuda, compile: False)
🔥 Starting warm-up (loading weights + compiling if enabled)...
Loading weights: 100%|████████| 290/290
✅ Warm-up complete! Model loaded and ready (took 12.3s)
🚀 API ready to accept requests!
```

### 2. Testar com torch.compile()

```bash
# thresholds.yaml:
# enable_compile: true
# warmup_on_startup: true

uvicorn app.api.main:app --reload
```

**Você verá:**
```
Loading pipeline (model: qwen, 4-bit: True, device: cuda, compile: True)
⚠️  torch.compile() ENABLED - Initial compilation will take 2-5 minutes...
🔥 Starting warm-up (loading weights + compiling if enabled)...
Loading weights: 100%|████████| 290/290
[Compiling... this takes 2-5 minutes, please wait...]
✅ Warm-up complete! Model compiled and ready (took 314.7s)
🚀 API ready to accept requests!
```

---

## 💡 Recomendações

### Para DESENVOLVIMENTO:
```yaml
enable_compile: false
warmup_on_startup: true
```
✅ Startup rápido (~15s)  
✅ Performance ótima para debug

### Para PRODUÇÃO (deploy normal):
```yaml
enable_compile: false
warmup_on_startup: true
```
✅ Startup rápido (~15s)  
✅ TRUE BATCH já é 81.7% mais rápido

### Para PRODUÇÃO (máxima performance):
```yaml
enable_compile: true
warmup_on_startup: true
```
⚡ +27% adicional sobre TRUE BATCH  
⚠️ Startup lento (3-7min) - OK para deploys longos

### Para JETSON (recurso limitado):
```yaml
enable_compile: false  # Jetson pode não suportar torch.compile
warmup_on_startup: true
use_4bit: true         # ESSENCIAL para VRAM limitada
```

---

## 🔍 Detalhes Técnicos

### O que acontece no Warm-up?

1. **Pipeline inicialização:** Configuração básica (~1s)
2. **Lazy loading trigger:** Primeira chamada força `_load_model()`
3. **Carregamento de pesos:** Download/cache + load VRAM (~10s)
4. **torch.compile() (se habilitado):**
   - Traça o grafo computacional do modelo
   - Otimiza operações (fusion, layout, etc.)
   - Gera código otimizado (~2-5min)
5. **Inferência dummy:** Valida funcionamento completo
6. **API ready:** Aceita requisições

### Por que a compilação demora?

- **First-time JIT compilation:** torch.compile() analisa o modelo na primeira execução
- **Graph tracing:** Mapeia todas operações do forward pass
- **Optimization passes:** Multiple passes de otimização
- **Code generation:** Gera código CUDA otimizado

### Por que vale a pena?

**Ganhos do torch.compile():**
- Kernel fusion (menos overhead)
- Memory layout optimization
- CUDA graph optimization
- Operações redundantes eliminadas

**Resultado:** +10-30% velocidade **em todas** as inferências seguintes

---

## 🎯 Checklist de Produção

- [ ] Definir configuração apropriada (`enable_compile` true/false)
- [ ] Garantir `warmup_on_startup: true`
- [ ] Testar startup time aceitável para seu deploy
- [ ] Validar que primeira requisição está rápida
- [ ] Benchmark performance com TRUE BATCH
- [ ] Se usando compile: aguardar 3-7min no deploy
- [ ] Logs mostram "API ready to accept requests!"

---

## ❓ FAQ

**Q: Devo usar torch.compile() em produção?**  
A: Depende:
- ✅ SIM se: deploys longos, infra estável, busca máxima performance
- ❌ NÃO se: deploys frequentes, startup time crítico, instabilidade

**Q: Posso desabilitar warm-up?**  
A: Tecnicamente sim (`warmup_on_startup: false`), mas **NÃO recomendado**.  
Primeira requisição ficará muito lenta (10-15s).

**Q: torch.compile() funciona no Jetson?**  
A: Depende da versão do PyTorch. JetPack >= 5.1 pode suportar, mas teste antes.  
Se falhar, fallback automático para modo normal.

**Q: E se eu reiniciar a API?**  
A: Warm-up roda novamente. Com compile: 3-7min toda reinicialização.  
**Solução:** Use hot-reload apenas para código, não para modelo.

**Q: Posso ver progresso da compilação?**  
A: torch.compile() é silencioso. Use logs para timing.  
Durante compilação, CPU está alta mas GPU idle.

---

## 📚 Referências

- TRUE BATCH: [tests/test_true_batch.py](tests/test_true_batch.py)
- torch.compile docs: https://pytorch.org/tutorials/intermediate/torch_compile_tutorial.html
- Performance findings: [OPTIMIZATION_FINDINGS.md](OPTIMIZATION_FINDINGS.md)
