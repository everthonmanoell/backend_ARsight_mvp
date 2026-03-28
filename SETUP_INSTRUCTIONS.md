# Setup Instructions — Configuração por Ambiente

Este projeto é otimizado para três ambientes de deployment distintos:

| Ambiente | Hardware | JetPack/OS | CUDA | Python | Deployment |
|----------|----------|-----------|------|--------|------------|
| Desktop Legion | RTX 3080/4090 | Ubuntu 22.04 | 12.1+ | 3.10+ | Poetry + `pyproject-legion.toml` |
| Jetson Orin | AGX Orin / Orin NX | JetPack 6.x (L4T R36) | 12.6 | 3.10 | Poetry + `pyproject.toml` (recomendado) |
| Jetson Nano | Jetson Nano | JetPack 4.6 (L4T R32) | 10.2 | 3.8 | Docker + `docker-compose-nano.yml` |

---

## Jetson Orin (Recomendado)

### 1. Verificar ambiente

```bash
# Confirme que tem L4T R36.x e CUDA 12.6
cat /etc/nv_tegra_release | grep "R36\|REVISION"
nvidia-smi  # deve mostrar CUDA 12.6+
python3 --version  # deve ser 3.10+
```

### 2. Instalação Nativa com Poetry

Ver [JETSON_SETUP.md](JETSON_SETUP.md) para guia rápido completo.

**Passo 1: Instalar dependências**
```bash
cd ~/backend_tcc_mvp
poetry install
```

**Passo 2: Instalar PyTorch com CUDA (obrigatório)**
```bash
poetry run pip install torch==2.8.0 --index-url https://pypi.jetson-ai-lab.io/jp6/cu126
```

**Passo 3: Validar**
```bash
poetry run python -c "import torch; print('torch:', torch.__version__); print('cuda:', torch.cuda.is_available())"
# Esperado: torch: 2.8.0, cuda: True
```

**Passo 4: Rodar API**
```bash
poetry run ar-api
```

CUDA e FP16 estão ativados automaticamente.

#### Configuração de Precisão (FP16/FP32)

O sistema detecta automaticamente a arquitetura do processador e seleciona FP16 para Jetson Orin:

```bash
# Modo padrão (FP16 automático)
poetry run ar-api

# Modo desenvolvimento com auto-reload
poetry run uvicorn app.api.main:app --reload --host 0.0.0.0 --port 8000
```

O módulo `app/config/config.py` detecta a arquitetura (aarch64) e seleciona FP16 automaticamente. Para forçar FP32 (fallback):
```bash
MODEL_PRECISION=fp32 poetry run ar-api
```

### 3. Testar a Instalação

```bash
# Health check
curl http://localhost:8000/health

# Diagnóstico de imagem
curl -X POST http://localhost:8000/diagnose \
  -F "file=@data/illumination/normal/normal_image1.jpg"

# Swagger UI
# Abrir navegador em: http://localhost:8000/docs
```

---

## Desktop Legion

### 1. Verificar ambiente

```bash
# CUDA 12.1+
nvidia-smi  # deve mostrar CUDA 12.1+
python3 --version  # deve ser 3.10+
```

### 2. Instalação com Poetry

```bash
cd ~/backend_tcc_mvp

# Copiar config de Desktop
cp pyproject-legion.toml pyproject.toml

# Instalar
poetry install
```

PyTorch (com CUDA 12.1+) é instalado automaticamente do PyPI.

**Validar:**
```bash
poetry run python -c "import torch; print('cuda:', torch.cuda.is_available())"
# Esperado: cuda: True
```

**Rodar:**
```bash
poetry run ar-api
```

### 3. Testar a Instalação

### 4. Desenvolvimento e Testes

No desktop é mais rápido fazer testes e ajustes:

```bash
# Rodar testes
poetry run pytest tests/

# Batch illumination test
poetry run python tests/test_illumination_batch.py

# Benchmark (Jetson vs Legion)
poetry run python benchmark_jetson_vs_legion.py
```

---

## Jetson Nano (Deprecado)

Jetson Nano é extremamente limitado em recursos computacionais e encontra-se ultrapassado. Recomenda-se fortemente a migração para Jetson Orin ou utilização de ambiente desktop. Para fins de arquivo técnico, se ainda necessário:

### Instalação com Docker (Única opção recomendada)

```bash
cd ~/backend_tcc_mvp

# Build imagem
make docker-build-nano

# Rodar container
make docker-run-nano

# OU com Docker Compose
make docker-up-nano
make docker-logs-nano
make docker-down-nano
```

---

## Configuração de Precisão (FP16 vs FP32)

### Justificativa para FP16

A Jetson Orin compartilha 32GB de memória unificada entre CPU e GPU. FP16 (half precision) reduz o consumo de memória em 50% sem degradação significativa da acurácia:

| Métrica | FP32 | FP16 |
|---------|------|------|
| Memória por modelo | 4GB | 2GB |
| Throughput | Baseline | ~2x mais rápido |
| Latência (Qwen 0.5B) | ~1s | ~0.5s |
| Acurácia | 100% | 99.5-99.8% |
| Suporte Orin | Sim | Sim (Tensor cores) |

### Indicações de FP16
- Modelos LLM (Qwen, Phi, Llama)
- Processamento em batch (múltiplas imagens)
- Aplicações em tempo real com múltiplas requisições
- Desenvolvimento com restrição de VRAM

### Quando usar FP32 (Fallback)
- Diagnóstico com artefatos visuais severos
- Falha de quantização 4-bit com FP16
- Problemas de convergência de modelo

### Configuração no projeto

```bash
# FP16 automático (padrão recomendado)
poetry run ar-api

# FP32 fallback (se FP16 causar problemas)
MODEL_PRECISION=fp32 poetry run ar-api
```

**Detectado automaticamente** em `app/config/config.py`:
- Jetson (aarch64) → FP16 (torch.float16)
- Desktop (x86_64) → FP32 (torch.float32)

Para verificar:
```bash
poetry run python tests/manual/test_gpu.py
# Verifica Device, DType, CUDA status
```

### Comparação de Desempenho

| Métrica | Desktop Legion | Jetson Orin | Jetson Nano |
|---------|---------------|------------|------------|
| Latência (Qwen 0.5B) | ~0.5s | ~1s | ~4-6s |
| VRAM (Phi-3) | 6GB | 2GB | Não suportado |
| CUDA Compute | 8.6+ | 8.7 | 5.3 |
| Quantização 4-bit | Suportado | Suportado | Não suportado |
| Custo | Alto | Médio | Baixo |

---

## Troubleshooting

### Poetry: `torch` não encontra wheel

**Orin:**
```bash
poetry cache clear --all
poetry lock --no-cache --regenerate
poetry install
```

**Desktop:**
```bash
# Verifique que está com pyproject-legion.toml
poetry lock --no-cache --regenerate
```

### Docker: `Error response from daemon: Unknown runtime specified nvidia`

```bash
# Reinstale ou reconfigure runtime
sudo apt-get install --reinstall nvidia-container-runtime  # Orin
docker info | grep -i runtime  # deve listar "nvidia"
```

### GPU não aparece no Docker

```bash
# Verifique:
docker run --rm --runtime=nvidia nvidia-smi

# Se falhar, reinstale:
sudo apt-get update
sudo apt-get install -y nvidia-container-toolkit nvidia-container-runtime
sudo systemctl restart docker
```

### CUDA Out of Memory (Orin)

Jetson Orin tem 32GB compartilhada entre CPU+GPU. Se receber erro:

```bash
# Monitore uso:
sudo tegrastats

# Se necessário, reduza workers ou batch size
# Editar app/config/thresholds.yaml
```

---

## 📝 Quick Reference

### Começar Com...

**Jetson Orin:**
```bash
poetry install
poetry run ar-api          # Automático FP16 + CUDA
```

**Jetson Orin (se FP16 falhar):**
```bash
MODEL_PRECISION=fp32 poetry run ar-api
```

**Desktop Desenvolvimento:**
```bash
cp pyproject-legion.toml pyproject.toml
poetry install && make dev
```

**Docker Nano:**
```bash
docker compose -f docker-compose-nano.yml up
```

---

## Próximos Passos

- [ ] Verificar versão do JetPack selecionado
- [ ] Escolher método de instalação (nativa ou Docker)
- [ ] Testar com `curl http://localhost:8000/health`
- [ ] Fazer deploy em produção
