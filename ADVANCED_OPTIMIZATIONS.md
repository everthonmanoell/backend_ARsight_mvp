# Otimizações Avançadas - Guia de Implementação

## 📊 Resumo de Performance Atual

| Método | Tempo/Imagem | Melhoria | Speedup |
|--------|--------------|----------|---------|
| Baseline (inicial) | 15.0s | - | 1.0x |
| Após otimizações simples | 5.28s | 64.8% | 2.84x |
| **TRUE BATCH (atual)** | **0.96s** | **93.6%** | **15.6x** |

## 🚀 Otimizações Disponíveis

### ✅ JÁ IMPLEMENTADAS

#### 1. TRUE BATCH INFERENCE
```python
# Múltiplos prompts em um único forward pass
# Implementado em: app/models/base_model.py, app/models/qwen_model.py
results = pipeline.diagnose_from_metrics_batch(images)
```
**Ganho:** 81.7% (5.48x speedup)  
**Status:** ✅ Produção

#### 2. torch.inference_mode()
```python
# Mais eficiente que torch.no_grad()
with torch.inference_mode():
    outputs = model.generate(...)
```
**Ganho:** ~5-10%  
**Status:** ✅ Produção

#### 3. Otimização de Parâmetros
```yaml
# thresholds.yaml
qwen:
  max_tokens: 60  # reduzido de 250
  temperature: 0.3  # reduzido de 0.6
```
**Ganho:** ~40-50%  
**Status:** ✅ Produção

#### 4. Prompt Engineering
```python
# Limita verbosidade do modelo
"Keep your explanation under 50 words and be very concise."
```
**Ganho:** ~10-15%  
**Status:** ✅ Produção

---

### 🔬 EXPERIMENTAIS (Disponíveis mas não testadas)

#### 5. BetterTransformer (Optimum)
**Descrição:** Otimização PyTorch nativa para Transformers  
**Ganho Esperado:** 5-15%  
**Complexidade:** Baixa (1 linha de código)

**Instalação:**
```bash
pip install optimum
```

**Uso:**
```python
# Já implementado em qwen_model.py!
# Ativa automaticamente se optimum estiver instalado
from optimum.bettertransformer import BetterTransformer
model = BetterTransformer.transform(model)
```

**Teste:**
```bash
# Instalar optimum
pip install optimum

# Executar pipeline - BetterTransformer ativa automaticamente
python tests/test_true_batch.py
```

**☑️ IMPLEMENTAÇÃO:** ✅ Código pronto em [qwen_model.py](app/models/qwen_model.py#L75-L83)

---

#### 6. torch.compile() (PyTorch 2.0+)
**Descrição:** Compilação JIT do modelo para otimização automática  
**Ganho Esperado:** 10-30%  
**Complexidade:** Baixa, mas alto overhead de inicialização

**Uso:**
```python
# Já tem suporte em qwen_model.py!
pipeline = IlluminationPipeline(
    model_name="qwen",
    enable_compile=True  # Ativa torch.compile()
)
```

**⚠️ IMPORTANTE:**
- Primeira compilação demora 2-5 minutos
- Após compilado, inferências são mais rápidas
- Melhor para produção com longa duração
- Não combina bem com BetterTransformer

**Teste:**
```bash
python tests/test_optimizations_advanced.py
```

**☑️ IMPLEMENTAÇÃO:** ✅ Código pronto com flag `enable_compile` em [qwen_model.py](app/models/qwen_model.py#L67-L73)

---

#### 7. Flash Attention 2
**Descrição:** Implementação otimizada de atenção (requer hardware específico)  
**Ganho Esperado:** 20-40%  
**Complexidade:** Média (requer recompilação)

**Requisitos:**
- GPU Compute Capability >= 8.0 (RTX 30xx, RTX 40xx, A100)
- CUDA 11.8+
- PyTorch 2.0+

**Instalação:**
```bash
pip install flash-attn --no-build-isolation
```

**Uso:**
```python
# Modificar em qwen_model.py na inicialização
self.model = AutoModelForCausalLM.from_pretrained(
    model_path,
    quantization_config=bnb_config,
    device_map="auto",
    trust_remote_code=True,
    attn_implementation="flash_attention_2"  # Adicionar esta linha
)
```

**Verificar suporte:**
```python
import torch
print(torch.cuda.get_device_capability())  # Deve ser >= (8, 0)
```

**Status:** 🔬 Para testar

---

#### 8. Speculative Decoding
**Descrição:** Usa modelo pequeno para draft + modelo grande para verificação  
**Ganho Esperado:** 2-3x  
**Complexidade:** Alta

**Conceito:**
```
1. Modelo draft (tiny) gera N tokens rapidamente
2. Modelo target (Qwen) verifica em paralelo
3. Aceita tokens corretos, descarta incorretos
```

**Implementação:**
- Requer modelo draft compatível (Qwen2-0.1B ou similar)
- Modificações extensas no código de geração
- Melhor custo-benefício de todas as otimizações avançadas

**Status:** 🔬 Para pesquisa futura

---

#### 9. Static KV Cache
**Descrição:** Pré-aloca cache de atenção para evitar realocações  
**Ganho Esperado:** 5-10%  
**Complexidade:** Baixa

**Uso:**
```python
# Adicionar em generate()
outputs = self.model.generate(
    input_ids,
    max_new_tokens=max_tokens,
    use_cache=True,
    cache_implementation="static"  # PyTorch 2.2+
)
```

**Status:** 🔬 Para testar

---

#### 10. Token Caching (Prompt Caching)
**Descrição:** Cache de prefixos de prompts repetidos  
**Ganho Esperado:** 10-20% (para prompts similares)  
**Complexidade:** Média

**Cenário ideal:**
```
Prompt 1: [SYSTEM_PROMPT] + [metrics scene 1]
Prompt 2: [SYSTEM_PROMPT] + [metrics scene 2]
         ^^^^^^^^^^^^^^^^^
         Pode ser cacheado!
```

**Implementação:**
- Requer cache manual de KV states
- Funciona bem com TRUE BATCH (todos compartilham system prompt)

**Status:** 🔬 Para pesquisa futura

---

## 📊 Priorização de Implementação

### Ganho Rápido (Low-Hanging Fruit)
1. **BetterTransformer** - 1 comando, 5-15% ganho
   ```bash
   pip install optimum
   # Já funciona automaticamente!
   ```

2. **Static KV Cache** - 1 linha, 5-10% ganho
   ```python
   cache_implementation="static"
   ```

### Médio Esforço, Alto Retorno
3. **torch.compile()** - Flag já implementada, 10-30% ganho
   - ⚠️ Teste primeiro: 2-5min de compilação inicial
   - Melhor para produção contínua

4. **Flash Attention 2** - Se GPU compatível, 20-40% ganho
   - Verificar Compute Capability primeiro
   - Pip install + 1 linha de código

### Alto Esforço, Pesquisa
5. **Speculative Decoding** - 2-3x ganho potencial
   - Requer modelo draft
   - Maior complexidade de implementação

6. **Prompt Caching** - 10-20% ganho
   - Funciona bem com batch processing
   - Requer implementação customizada

---

## 🧪 Como Testar

### Teste 1: BetterTransformer
```bash
# Instalar
pip install optimum

# Testar (detecta automaticamente)
python tests/test_true_batch.py

# Verificar logs - deve aparecer:
# "✅ BetterTransformer enabled"
```

### Teste 2: torch.compile()
```bash
# Executar benchmark de otimizações
python tests/test_optimizations_advanced.py

# Compara:
# - Baseline (sem otimizações extras)
# - torch.compile() (modo reduce-overhead)
```

### Teste 3: Flash Attention 2
```bash
# Verificar compatibilidade
python -c "import torch; print(torch.cuda.get_device_capability())"
# Precisa >= (8, 0)

# Instalar (pode demorar ~10min)
pip install flash-attn --no-build-isolation

# Modificar qwen_model.py (adicionar attn_implementation)
# Testar
python tests/test_true_batch.py
```

---

## 📈 Roadmap de Otimizações

### Fase 1: Ganhos Rápidos (Esta Semana) ✅
- [x] TRUE BATCH INFERENCE → 93.6% mais rápido
- [x] torch.inference_mode()
- [x] Otimização de parâmetros
- [x] Prompt engineering

### Fase 2: Otimizações Experimentais (Próxima Semana)
- [ ] **BetterTransformer** - Testar (5-15% esperado)
- [ ] **Static KV Cache** - Implementar (5-10% esperado)
- [ ] **torch.compile()** - Benchmark produção (10-30% esperado)

### Fase 3: Otimizações Avançadas (Pesquisa)
- [ ] **Flash Attention 2** - Se hardware compatível (20-40% esperado)
- [ ] **Speculative Decoding** - Prova de conceito (2-3x esperado)
- [ ] **Prompt Caching** - Implementação customizada (10-20% esperado)

---

## 🎯 Meta de Performance

| Métrica | Atual (TRUE BATCH) | Meta Fase 2 | Meta Fase 3 |
|---------|-------------------|-------------|-------------|
| Tempo/imagem (batch 8) | 0.96s | 0.70s | 0.40s |
| Speedup vs Baseline | 15.6x | ~21x | ~37x |
| Melhoria adicional | - | +27% | +58% |

---

## 💡 Recomendações

### Para Produção Imediata
✅ **Usar TRUE BATCH** - já validado, 93.6% mais rápido  
✅ **Batch size: 4-8** imagens (RTX 3060 6GB VRAM)  
✅ **max_tokens=60, temperature=0.3** - configuração atual  

### Para Experimentação
🔬 **BetterTransformer** - baixo risco, fácil instalação  
🔬 **Static KV Cache** - uma linha de código  
⚠️ **torch.compile()** - testar overhead de inicialização  

### Para Hardware Específico
🎯 **Flash Attention 2** - se GPU >= RTX 3060 (Compute 8.0+)  
🎯 **Jetson deployment** - testar batch size menores (2-4)  

---

## 📞 Suporte

**Documentos relacionados:**
- [OPTIMIZATIONS.py](OPTIMIZATIONS.py) - Histórico completo de otimizações
- [test_true_batch.py](tests/test_true_batch.py) - Benchmark TRUE BATCH
- [test_optimizations_advanced.py](tests/test_optimizations_advanced.py) - Benchmark de otimizações experimentais

**Logs de performance:**
- Procurar por "⚡" nos logs para métricas de batch
- Procurar por "✅" para confirmação de otimizações ativadas
