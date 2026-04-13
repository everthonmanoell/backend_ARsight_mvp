# 🔧 Rollback Parcial - DialoGPT-small Nano

## 📊 Diagnóstico

O modelo ficou muito "solto demais" na tentativa anterior:
- **Tempo:** 17.3s de SLM (era 2.9s) → **5.9x mais lento**
- **Qualidade:** Alucinações evidentes com fragmentos métricos soltos
- **Culpados:** Prompts muito abertos + geração longa + sem validação

## ✅ Rollback Aplicado

### 1. Redução de Tokens

```yaml
# Antes
max_tokens: 30
summary_tokens: 40

# Depois
max_tokens: 20          # Reduzido em 33%
summary_tokens: 32      # Reduzido em 20%
```

**Impacto esperado:** Menos tempo, menos espaço para "viagem" do modelo.

### 2. Prompts Muito Mais Curtos e Fechados

**Antes (muito longo e aberto):**
```python
prompt = (
    f"AR lighting check. "
    f"Status: {status}. "
    f"Risk: {risk_level}. "
    f"Label: {illumination_label}. "
    f"Brightness: {mean_luma:.0f}/255. "
    f"Uniformity: {uniformity:.0%}. "
    f"Dark clipping: {pct_dark:.1%}. "
    f"Bright clipping: {pct_bright:.1%}. "
    f"Write one natural sentence. "
    f"Explain whether this scene is good for AR."
)
```

**Depois (curto, claro, fechado):**
```python
# Exemplo para PASS:
prompt = (
    f"AR lighting analysis. "
    f"Brightness {mean_luma:.0f}, uniformity {uniformity:.0%}. "
    f"This is good for AR. One sentence."
)

# Exemplo para FAIL:
prompt = (
    f"Scene is {illumination_label}. "
    f"Brightness {mean_luma:.0f}/255. "
    f"Explain briefly why AR tracking is affected."
)
```

**Impacto:** Menos espaço de fuga, contexto muito bem definido.

### 3. Validação Forte Contra "Junk"

**Novo método `_postprocess_dialogpt_text()`:**

Detecta e **rejeita** respostas com artefatos óbvios:

```python
junk_indicators = [
    "I.",                    # Começo estranho
    "edit formatting",       # Meta-coment
    "13 14 15 16 17",       # Números soltos
    "1,2, 3 and 4 5 7",     # Contagem aberrante
    "Lightpassing",          # Não-palavra
]

# Se detecta junk → retorna None
# → SLM ativa fallback do sistema (template limpo)
```

### 4. Fallback Inteligente

**Antes:** Resposta curta → reaproveita output completo
```python
if not response or len(response) < 10:
    response = self.tokenizer.decode(outputs[0], ...)  # Pode vir ecoado
```

**Depois:** Resposta ruim → fallback limpo
```python
if not response or len(response.strip()) < 8:
    return ""  # Deixa base usar template
    
cleaned = self._postprocess_dialogpt_text(response)
if cleaned is None:
    return ""  # Junk → template ao invés de lixo
```

## 🎯 Resultado Esperado

| Métrica | Antes (ruim) | Esperado (depois) |
|---------|-------------|-------------------|
| SLM time | 17.3s | ~3-4s |
| Frames com junk | ~3/10 | 0/10 |
| Resposta típica | "I. Lighting : 0, ..." | "Low light reduces AR tracking." |
| Fallback % | ~0% usado | ~20-30% (quando SLM falha) |

## 🚀 Como Testar

```bash
# Terminal 1: API
poetry run ar-api

# Terminal 2: Teste
python test_batch_flow.py
```

**Procure no JSON:**
- ✅ `slm_total_s` próximo a 3-4s (era 17.3s)
- ✅ Nenhuma `explanation` com "I.", "edit", números soltos
- ✅ Summary ainda bom (era OK antes)
- ✅ Fallback templates quando necessário

## 📝 Filosofia desta Mudança

DeğilhaGPT-small (117M params) **precisa de rédea curta**:

- ✅ Greedy decoding (True) → determinístico
- ✅ Tokens baixos (20) → menos espaço para improviso
- ✅ Prompts curtos → contexto limpo
- ✅ Validação forte → rejeita lixo cedo

Isso **não** tira qualidade:
- Explicações são concisas mas naturais
- Fallback templates preenchem lacunas
- Summary ainda interpreta dados bem

## 🎓 Lição Aprendida

Uma arquitetura híbrida (Rule Engine + SLM + Templates) não precisa que o SLM acerte **sempre**.

O SLM pode:
- Gerar bem ~70% das vezes
- Falhar ~30% das vezes
- E ter fallback silencioso para template

Isso é **mais eficiente e robusto** que forçar um modelo pequeno a ser perfeito.
