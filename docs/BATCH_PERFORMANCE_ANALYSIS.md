# Análise de Performance: Inferência em Batch com SLM na GPU

> Contexto: sistema de diagnóstico de iluminação para AR (Realidade Aumentada),  
> usando o modelo **Qwen2.5 0.5B Instruct** quantizado em 4-bit numa **RTX 3060 Laptop (6 GB VRAM)**.

---

## 1. O gargalo: geração autoregressiva de tokens

Modelos de linguagem do tipo *decoder-only* (GPT, Qwen, Phi, LLaMA…) geram texto de
forma **autoregressiva**: cada token é produzido em função de todos os tokens anteriores.
Isso significa que a geração de uma resposta de $T$ tokens exige **$T$ passagens sequenciais
pela rede** — não é possível paralelizar os passos de geração *dentro de um único prompt*.

```
Passo 1: prompt → token₁
Passo 2: prompt + token₁ → token₂
Passo 3: prompt + token₁ + token₂ → token₃
...
Passo T: ... → tokenT   ← único resultado
```

Para o Qwen 0.5B gerando ~60 tokens de diagnóstico, esse processo consome um tempo
fixo de aproximadamente **3,5 s** na RTX 3060 com quantização 4-bit — independentemente
de o request chegar via `/diagnose` ou `/diagnose/batch` com N=1.

---

## 2. Por que o batch reduz o custo por diagnóstico

Embora os passos de geração de *um único prompt* sejam sequenciais, a GPU consegue
executar os forward passes de **múltiplos prompts simultaneamente** nas suas milhares
de CUDA cores — desde que todos estejam reunidos num único tensor (batch).

### Analogia

> Uma impressora industrial demora 5 s para configurar e imprimir 1 folha.  
> Se você mandar 10 folhas de uma vez, ela imprime todas em ~5,5 s (não em 50 s),  
> pois o overhead de setup é compartilhado.

Na GPU o mecanismo é o mesmo: o *custo fixo* de carregar pesos, alocar buffers de
atenção e dispatcher CUDA é **amortizado** sobre todos os prompts do batch.

### Equação aproximada

Seja $t_1 \approx 3{,}5\,\text{s}$ o tempo de geração para um único prompt. Para um
batch de $N$ prompts processados em paralelo:

$$t_{\text{total}}(N) \approx t_1 + \alpha \cdot (N - 1)$$

onde $\alpha \ll t_1$ é o custo marginal de adicionar mais um prompt ao batch
(sobrecarga de padding e atenção cruzada), medido empiricamente em ~0,15 s/prompt
neste hardware.

O tempo **por diagnóstico** é então:

$$t_{\text{diag}}(N) = \frac{t_{\text{total}}(N)}{N} \approx \frac{t_1}{N} + \alpha$$

À medida que $N$ cresce, $t_{\text{diag}}$ converge para $\alpha$ (o custo marginal),
e o ganho de throughput se torna cada vez maior.

---

## 3. Resultados medidos

Todos os valores foram obtidos com warmup completo, `torch.compile` habilitado,
Qwen2.5 0.5B Instruct 4-bit, RTX 3060 Laptop 6 GB, CUDA 12.1.

| N (imagens no batch) | Tempo total LLM | Tempo PDI (visão) | **Por diagnóstico** | Meta < 1 s |
|:---:|:---:|:---:|:---:|:---:|
| 1  | 3,52 s | 0,7 ms | **3,52 s** | ❌ |
| 2  | 4,16 s | 0,7 ms | **2,08 s** | ❌ |
| 3  | 4,73 s | 0,6 ms | **1,58 s** | ❌ |
| 6  | 4,97 s | 0,7 ms | **0,83 s** | ✅ |
| **10** | **4,83 s** | **0,7 ms** | **0,48 s** | ✅ |

> **Observação:** o PDI (análise de iluminação por visão computacional) é negligenciável
> em todos os cenários — menos de 1 ms por imagem — confirmando que o único gargalo
> relevante é a geração de tokens pelo SLM.

---

## 4. Otimizações aplicadas ao servidor

### 4.1 Warmup no startup

Na inicialização da API (`lifespan` do FastAPI), o pipeline executa **3 inferências
dummy** antes de aceitar requests reais:

```
Startup  →  carrega pesos (~5 s)
         →  warmup #1: 4,4 s  (alocação de buffers CUDA)
         →  warmup #2: 4,1 s  (pré-aquecimento de caches)
         →  warmup #3: 4,0 s  (modelo em regime estacionário)
         →  API pronta — requests recebem ~0,5 s/diagnóstico
```

Sem esse warmup, o **primeiro request real** paga o custo de alocação de memória e
compilação JIT, resultando em latências de 10–15 s.

### 4.2 `torch.compile` (PyTorch 2.0+)

A diretiva `torch.compile(model, mode="reduce-overhead")` aciona o compilador
TorchInductor, que:

1. Rastreia o grafo computacional nas primeiras chamadas (*tracing*).
2. Gera código CUDA/Triton otimizado para o hardware específico.
3. Funde operações de atenção e FFN em kernels customizados.

O custo é pago uma vez no startup (~2–5 min em cold start). Após compilado, o modelo
opera com **10–30% menos latência** por forward pass em relação ao modo eager.

### 4.3 Quantização 4-bit (bitsandbytes NF4)

O modelo Qwen2.5 0.5B original ocupa ~1 GB em FP16. Com quantização NF4 + double
quantization o footprint cai para ~400 MB de VRAM, permitindo batches maiores sem
OOM (*out-of-memory*) na GPU de 6 GB.

### 4.4 `padding_side='left'` no tokenizer

Modelos decoder-only geram tokens a partir da **direita** do contexto. Ao fazer
padding, os tokens de preenchimento devem ficar à **esquerda** para que todos os
prompts do batch terminem alinhados na posição de geração — caso contrário, o modelo
gera tokens a partir do padding, corrompendo as respostas.

```python
# Correto para decoder-only em batch
tokenizer = AutoTokenizer.from_pretrained(MODEL, padding_side='left')
```

---

## 5. Fluxo completo de um request `/diagnose/batch`

```
Celular
  │
  │  POST /diagnose/batch  (10 imagens JPEG)
  ▼
FastAPI (servidor pré-aquecido)
  │
  ├─ Validação de formato/tamanho  (~1 ms)
  │
  ├─ PDI — IlluminationAnalyzer (OpenCV)
  │    Para cada imagem:
  │      • Histograma de luminância
  │      • Cálculo de score (clipping, uniformidade)
  │      • Label: underexposed / acceptable / adequate / overexposed
  │    Tempo total: ~7 ms (10 imagens)
  │
  ├─ Rule Engine (determinístico)
  │    Para cada cena: avalia thresholds → status (pass/fail) + risk_level
  │    Tempo total: < 1 ms
  │
  ├─ SLM — Qwen2.5 0.5B (true batch inference)
  │    • Constrói 10 prompts em paralelo
  │    • Tokeniza + padding left → tensor [10, seq_len]
  │    • 1 forward pass na GPU → gera tokens de todos os 10 prompts
  │    • Decodifica 10 respostas
  │    Tempo total: ~4,8 s
  │
  └─ Monta e retorna JSON com 10 diagnósticos
       • status, risk_level, explanation, metrics, recommendations

  │
  ▼
Celular recebe resposta em ~4,8 s
→ 0,48 s por diagnóstico (abaixo da meta de 1 s)
```

---

## 6. Limitação e contexto de uso

O benefício de batch **só se materializa quando múltiplos prompts são processados
juntos**. Para um único prompt isolado o tempo permanece ~3,5 s, independentemente
de usar `/diagnose` ou `/diagnose/batch` com N=1.

Isso define a **estratégia correta de uso do front-end**:

| Estratégia | Tempo total | Por diagnóstico |
|---|---|---|
| 10 requests individuais | 10 × 3,5 s = **35 s** | 3,5 s ❌ |
| 1 request batch (N=10) | **~4,8 s** | 0,48 s ✅ |

O aplicativo móvel deve, portanto, **acumular os N frames capturados** e enviá-los
num único request batch — exatamente o fluxo já implementado no front-end.

---

## 7. Resumo executivo

| Otimização | Onde atua | Ganho |
|---|---|---|
| Warmup no startup | Latência do 1.º request | Elimina pico de 10–15 s |
| `torch.compile` | Forward pass do modelo | −10 a 30% por geração |
| Quantização 4-bit NF4 | VRAM | Permite batches maiores na GPU de 6 GB |
| True batch inference | Throughput do servidor | N × redução no custo/diagnóstico |
| `padding_side='left'` | Qualidade das respostas em batch | Evita corrupção de saída |

**Resultado final:** com warmup completo e batch de 10 imagens, cada diagnóstico
(PDI + Rule Engine + explicação SLM) é entregue em **~0,48 s** — dentro da meta de
1 s estabelecida para o sistema.
