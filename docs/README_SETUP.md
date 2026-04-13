# Documentation Index

Documentação completa do **AR Diagnostic MVP** — setup, deployment, e uso em diferentes ambientes.

## 📚 Guias por Ambiente

Escolha seu ambiente e siga o guia correspondente:

### 🔵 **Jetson Nano** (4GB VRAM)
📖 [JETSON_NANO_GUIDE.md](JETSON_NANO_GUIDE.md)

- **Modelo recomendado:** DialoGPT-small (117M params)
- **Latência:** ~3.4s (batch 10 frames)
- **Setup:** Local com Poetry ou Docker
- **Deployment:** Docker Compose (recomendado)

```bash
# Quick start
cd ~/backend_tcc_mvp
poetry run ar-api
```

---

### 🟢 **Jetson Orin** (8-32GB VRAM)
📖 [JETSON_ORIN_GUIDE.md](JETSON_ORIN_GUIDE.md)

- **Modelo recomendado:** Qwen2.5-0.5B (494M params)
- **Latência:** ~3.5s (batch 10 frames)
- **Alternativa:** Phi-3-mini (3.8B params) se latência > 5s aceita
- **Setup:** Local com Poetry ou Docker
- **Deployment:** Docker (JetPack 5.x)

```bash
cd ~/backend_tcc_mvp
poetry run ar-api
```

---

### 🔴 **Legion Desktop (RTX GPU)**
📖 [LEGION_GUIDE.md](LEGION_GUIDE.md)

- **Modelo recomendado:** Phi-3-mini (3.8B params)
- **Latência:** ~3-4s (batch 10 frames)
- **Alternativa:** Qwen2.5-0.5B se quer mais velocidade
- **Setup:** Automático via `setup_legion.ps1` (Windows)
- **Deployment:** Docker ou Poetry

```powershell
cd backend_tcc_mvp
.\setup_legion.ps1
poetry run ar-api
```

---

## 📋 Seleção de Modelos

📖 [MODEL_SELECTION.md](MODEL_SELECTION.md)

Explicação detalhada dos 3 modelos disponíveis:

| Modelo | Tamanho | VRAM | Jetson Nano | Jetson Orin | Legion |
|--------|---------|------|---|---|---|
| **DialoGPT-small** | 117M | 250 MB | ✅ Recomendado | ✅ Funciona | ✅ Rápido |
| **Qwen2.5-0.5B** | 494M | 1 GB | ⚠️ Lento | ✅ Recomendado | ✅ Funciona |
| **Phi-3-mini** | 3.8B | 7.6 GB | ❌ Não cabe | ✅ Funciona | ✅ Recomendado |

---

## 🔧 Setup Scripts

Na **raiz** do projeto já existem scripts prontos:

```bash
# Jetson Nano — Python 3.6 (estável)
bash setup_jetson_nano.sh

# Jetson Orin — Python 3.8+
bash setup_jetson_orin.sh

# Legion Windows — PowerShell
.\setup_legion.ps1
```

---

## 🧪 Documentação Técnica

### WINDOWS_CUDA_SETUP.md
📖 [WINDOWS_CUDA_SETUP.md](WINDOWS_CUDA_SETUP.md)

Referência técnica para configuração CUDA no Windows:
- Instalação de drivers NVIDIA
- Troubleshooting de CUDA
- Performance tuning
- FAQ técnico

*(Nota: Use LEGION_GUIDE.md como ponto de entrada; este é referência técnica)*

---

## 📊 Estado do Projeto

### ✅ Validado

- ✅ **Frame Upload** — 10/10 acceptance (EXIF handling fixed)
- ✅ **DialoGPT Performance** — 3.4s batch (target met)
- ✅ **Hallucination Detection** — 8 critérios implementados
- ✅ **Mixed Lighting Detection** — "inadequate lighting" label
- ✅ **Summary Diversity** — 5 templates por caso
- ✅ **Rule Engine (PDI)** — ~91 ms/frame

### 📊 Modelos Testados

| Modelo | Jetson Nano | Jetson Orin | Legion | Status |
|--------|---|---|---|---|
| DialoGPT-small | ✅ | ✅ | ✅ | Produção |
| Qwen2.5-0.5B | ⚠️ Experimental | ✅ | ✅ | Produção |
| Phi-3-mini | ❌ | ✅ | ✅ | Produção |

---

## 🗂️ Estrutura dos Docs

```
docs/
├─ README_SETUP.md (este arquivo)      ← Start here
├─ MODEL_SELECTION.md                  ← Explicação dos modelos
├─ JETSON_NANO_GUIDE.md                ← Setup Nano (4GB)
├─ JETSON_ORIN_GUIDE.md                ← Setup Orin (8-32GB)
├─ LEGION_GUIDE.md                     ← Setup Legion RTX
├─ WINDOWS_CUDA_SETUP.md               ← Ref técnica Windows (opcional)
└─ (antigos — manter por referência)
   ├─ JETSON_DEPLOYMENT.md             → Consolidado em JETSON_NANO_GUIDE.md
   ├─ JETSON_SETUP.md                  → Consolidado em JETSON_ORIN_GUIDE.md
   ├─ NANO_GUIDE.md                    → Consolidado em JETSON_NANO_GUIDE.md
   └─ NANO_POETRY_VS_DOCKER.md         → Referência (Docker vs Poetry)
```

---

## 🚀 Quick Start

### 1. Escolha seu ambiente

- Jetson Nano → [JETSON_NANO_GUIDE.md](JETSON_NANO_GUIDE.md)
- Jetson Orin → [JETSON_ORIN_GUIDE.md](JETSON_ORIN_GUIDE.md)
- Legion RTX → [LEGION_GUIDE.md](LEGION_GUIDE.md)

### 2. Execute o setup

```bash
# Linux (Jetson)
bash setup_jetson_nano.sh    # ou setup_jetson_orin.sh

# Windows (Legion)
.\setup_legion.ps1
```

### 3. Configure o modelo (opcional)

Editar `app/config/thresholds.yaml`:
```yaml
models:
  default: dialogpt    # ou qwen, phi
```

Ver [MODEL_SELECTION.md](MODEL_SELECTION.md) para recomendações.

### 4. Rodar a API

```bash
poetry run ar-api
# Acessa: http://localhost:8000
```

---

## 🔍 Troubleshooting Rápido

### Setup falhando?

1. Verificar pré-requisitos no seu guia específico
2. Executar comando de validação (CUDA, Python, etc)
3. Ler seção "Troubleshooting" do guia

### API não inicia?

1. Verificar `poetry run python -c "import torch"`
2. Checar `app/config/thresholds.yaml` (modelo válido?)
3. Ver logs: `docker logs -f ar-diagnostic-mvp`

### Performance ruim?

Ver [MODEL_SELECTION.md](MODEL_SELECTION.md) — talvez modelo inadequado para hardware.

---

## ❓ FAQ Geral

**P: Por onde começo?**  
A: Escolha seu hardware acima, clique no guia, e siga os passos.

**P: Qual modelo devo usar?**  
A: Consulte [MODEL_SELECTION.md](MODEL_SELECTION.md) e a tabela de recomendações.

**P: Posso mudar de modelo depois?**  
A: Sim. Editar `app/config/thresholds.yaml` e reiniciar.

**P: Docker ou Poetry?**  
A: **Docker** para produção (isolamento, reprodutibilidade).  
**Poetry** para desenvolvimento (iteração rápida).

**P: Os docs estão desatualizados?**  
A: Esses novos docs (2026-04-13) refletem o estado atual. Se encontrar inconsistências, reportar.

---

## 📞 Support

Se encontrar problemas:

1. Consulte **Troubleshooting** no seu guia específico
2. Verifique FAQ seção
3. Revise MODEL_SELECTION.md para certeza do modelo/hardware

---

## 📝 Última Atualização

**2026-04-13** — Reorganização completa de docs

- ✅ Consolidado JETSON_NANO_GUIDE.md (antes espalhado)
- ✅ Consolidado JETSON_ORIN_GUIDE.md (novo)
- ✅ Consolidado LEGION_GUIDE.md (antes setup_legion.ps1)
- ✅ Criado MODEL_SELECTION.md (novo)
- ✅ Criado README_SETUP.md (este arquivo)
- ✅ Mantido WINDOWS_CUDA_SETUP.md como referência

---
