# Setup Instructions — Configuração por Ambiente

**⚠️ ATENÇÃO:** Instruções de setup foram reorganizadas na pasta [setup/](setup/).

Este arquivo agora serve como índice. Consulte os documentos na pasta setup/ para instruções completas e atualizadas.

---

## 🐧 Jetson Orin (Linux / JetPack 6.x)

**Documentação completa:** [setup/jetson-orin/README.md](setup/jetson-orin/README.md)

**Setup rápido:**
```bash
cd ~/backend_tcc_mvp
bash setup/jetson-orin/setup.sh
poetry run ar-api
```

---

## 🪟 Desktop Legion (Windows)

**Documentação completa:** [setup/legion-windows/README.md](setup/legion-windows/README.md)

**Setup rápido:**
```powershell
cd C:\Users\<seu_usuario>\TCC\backend_tcc_mvp
.\setup\legion-windows\setup.ps1
poetry run ar-api
```

---

## 🔧 Troubleshooting

**Guia de solução de problemas:** [setup/TROUBLESHOOTING.md](setup/TROUBLESHOOTING.md)

---

## 📁 Estrutura de Setup

```
setup/
├── README.md                          (índice geral)
├── TROUBLESHOOTING.md                 (soluções comuns)
├── jetson-orin/
│   ├── setup.sh                       (script automático)
│   └── README.md                      (instruções detalhadas)
└── legion-windows/
    ├── setup.ps1                      (script automático)
    └── README.md                      (instruções detalhadas)
```

---

## 📚 Documentação Adicional

- [README.md](README.md) - Visão geral do projeto
- [JETSON_SETUP.md](JETSON_SETUP.md) - Detalhes específicos (legacy)
- [WINDOWS_CUDA_SETUP.md](WINDOWS_CUDA_SETUP.md) - Guia CUDA para Windows (legacy)

**Última atualização:** Abril 2026

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

## Desktop Legion (Windows)

### 1. Verificar ambiente

```powershell
# CUDA 12.1+
nvidia-smi  # deve mostrar CUDA 12.1+
python --version  # deve ser 3.10+
poetry --version  # deve estar instalado
```

### 2. Instalação com Poetry (Automático)

**Opção A: PowerShell (Recomendado)**
```powershell
cd backend_tcc_mvp
.\setup_legion.ps1
```

**Opção B: Command Prompt (cmd)**
```cmd
cd backend_tcc_mvp
setup_legion.bat
```

**Opção C: Manual**
```powershell
# Trocar configuração para Legion
Move-Item pyproject.toml pyproject-jetson.toml -Force
Move-Item pyproject-legion.toml pyproject.toml -Force

# Reconstruir lock
Remove-Item poetry.lock -Force
poetry lock

# Instalar dependências (PyTorch com CUDA 12.1+)
poetry install
```

### 3. Validar Instalação

```powershell
poetry run python -c "import torch; print(f'PyTorch: {torch.__version__}'); print(f'CUDA disponível: {torch.cuda.is_available()}'); print(f'Dispositivo CUDA: {torch.cuda.get_device_name(0) if torch.cuda.is_available() else \"N/A\"}')"
# Esperado: cuda: True
```

### 4. Rodar API

```powershell
poetry run ar-api
```

Acesse em: [http://localhost:8000/docs](http://localhost:8000/docs)

### 5. Testes e Benchmarks

No desktop é mais rápido fazer testes e ajustes:

```powershell
# Health check
curl http://localhost:8000/health

# Rodar testes unitários
poetry run pytest tests/

# Teste de batch
poetry run python tests/test_illumination_batch.py

# Benchmark (Jetson vs Legion)
poetry run python benchmark_jetson_vs_legion.py
```

---

## Desktop Legion (Linux)

### 1. Verificar ambiente

```bash
# CUDA 12.1+
nvidia-smi  # deve mostrar CUDA 12.1+
python3 --version  # deve ser 3.10+
poetry --version  # deve estar instalado
```

### 2. Instalação com Poetry (Automático)

```bash
cd backend_tcc_mvp
bash setup_legion.sh
```

O script `setup_legion.sh` faz:
- ✅ Troca para pyproject-legion.toml
- ✅ Reconstrói poetry.lock
- ✅ Instala dependências (incluindo PyTorch com CUDA)
- ✅ Valida disponibilidade de CUDA

### 3. Validar Instalação

```bash
poetry run python -c "import torch; print(f'PyTorch: {torch.__version__}'); print(f'CUDA: {torch.cuda.is_available()}')"
# Esperado: True
```

### 4. Rodar API

```bash
poetry run ar-api
```

Acesse em: [http://localhost:8000/docs](http://localhost:8000/docs)

### 5. Testes e Benchmarks

```bash
# Health check
curl http://localhost:8000/health

# Rodar testes
poetry run pytest tests/

# Batch illumination test
poetry run python tests/test_illumination_batch.py

# Benchmark
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

---

## Troubleshooting

### Windows - CUDA não encontrado

**Solução:**
```powershell
# 1. Verifique drivers NVIDIA
nvidia-smi

# 2. Se nvidia-smi não funciona:
# - Reinstale drivers da NVIDIA (versão 550+)
# - Download: https://www.nvidia.com/Download/driverDetails.aspx/

# 3. Reinstale PyTorch com CUDA 12.1
poetry run pip install --force-reinstall torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121

# 4. Valide novamente
poetry run python -c "import torch; print(torch.cuda.is_available())"
```

### Windows - Poetry lock falha

```powershell
# Limpe cache e tente novamente
poetry cache clear --all
Remove-Item poetry.lock -Force
poetry lock --no-cache --regenerate
poetry install
```

### Windows - Scripts não executam (erro de execução)

```powershell
# Se setup_legion.ps1 não executa:
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Depois tente novamente:
.\setup_legion.ps1
```

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
