# Jetson Orin Setup & Deployment Guide

Guia completo para setup e deploy do AR Diagnostic MVP no **Jetson Orin** com **JetPack 5.x+** (L4T R35.x).

> **Recomendação:** Usar **Qwen2.5-0.5B** para melhor balanço qualidade/performance. Ver [MODEL_SELECTION.md](MODEL_SELECTION.md) para comparação.

## ✅ Hardware Suportado

| Modelo | RAM | JetPack | L4T | CUDA | Status |
|---|---|---|---|---|---|
| **Jetson Orin Nano** | 8GB | 5.x+ | R35+ | 11.4 | ✅ Testado |
| **Jetson Orin NX** | 8GB | 5.x+ | R35+ | 11.4 | ✅ Compatível |
| **Jetson AGX Orin** | 32GB | 5.x+ | R35+ | 11.4 | ✅ Compatível |

---

## ⚠️ Diferenças vs. Jetson Nano

| Aspecto | Nano | Orin | Impacto |
|---|---|---|---|
| **RAM** | 4 GB | 8-32 GB | Orin pode rodar Phi-3 |
| **JetPack** | 4.6 | 5.x+ | Diferentes drivers/CUDA |
| **CUDA** | 10.2 | 11.4 | Melhor support |
| **GPU Compute** | 5.3 | 8.7 | Suporta quantização |
| **Performance** | ~3.4s (batch 10) | ~3.5s (batch 10) | Similar para Qwen |

---

## 📋 Pré-requisitos

### 1. Verificar JetPack
```bash
cat /etc/nv_tegra_release
# Esperado: L4T R35.x (JetPack 5.x)
```

### 2. Docker + NVIDIA Runtime

```bash
sudo apt-get update
sudo apt-get install -y docker.io

# NVIDIA Container Runtime (diferente do Nano)
sudo apt-get install -y nvidia-container-runtime

# Daemon config
sudo mkdir -p /etc/docker
sudo tee /etc/docker/daemon.json <<EOF
{
  "runtimes": {
    "nvidia": {
      "path": "nvidia-container-runtime",
      "runtimeArgs": []
    }
  }
}
EOF
sudo systemctl restart docker

# Testar
docker run --rm --runtime=nvidia nvcr.io/nvidia/l4t-base:r35.4.1 nvidia-smi
```

### 3. Python 3.8+ (já vem)
```bash
python3 --version  # Esperado: 3.8.x ou 3.10.x
```

### 4. Poetry
```bash
curl -sSL https://install.python-poetry.org | python3 -
export PATH="$HOME/.local/bin:$PATH"
```

---

## 🚀 Setup Local

### Com Poetry

```bash
cd ~/backend_tcc_mvp

# Usar configuração Jetson (genérico, funciona para Nano e Orin)
cp pyproject-jetson.toml pyproject.toml

# Opcional: se tiver pyproject-jetson-orin.toml customizado
# cp pyproject-jetson-orin.toml pyproject.toml

# Instalar
poetry install

# Rodar
poetry run ar-api
```

### Com pip

```bash
cd ~/backend_tcc_mvp

pip install -r requirements-jetson.txt

python3 -m uvicorn app.api.main:app --host 0.0.0.0 --port 8000
```

---

## 🐳 Setup Docker

### Build

```bash
cd ~/backend_tcc_mvp

# Dockerfile genérico funciona para Orin (base L4T R35)
docker build -f docker/Dockerfile.jetson \
  -t ar-diagnostic-mvp:jetson-orin .
```

### Run

```bash
docker run --rm \
  --runtime=nvidia \
  -e NVIDIA_VISIBLE_DEVICES=all \
  -e NVIDIA_DRIVER_CAPABILITIES=compute,utility \
  -p 8000:8000 \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/logs:/app/logs \
  ar-diagnostic-mvp:jetson-orin
```

### Com Docker Compose

```bash
# Usar compose genérico ou criar jetson-orin específico
docker-compose up -d

# Logs
docker-compose logs -f

# Parar
docker-compose down
```

---

## ⚙️ Configuração (YAML)

### Recomendação: Qwen2.5-0.5B

```yaml
models:
  default: qwen              # Qualidade excelente + performance boa
  device: cuda
  precision: fp16
  use_4bit: false            # Orin suporta, mas não necessário

qwen_config:
  model_path: "/home/user/models/Qwen2.5-0.5B-Instruct"
  prompt_max_length: 128
  max_tokens: 20
  summary_max_tokens: 32
  temperature: 0.2
  top_p: 0.9
  greedy_decoding: true
```

### Alternativa: Phi-3-mini (mais lento)

```yaml
models:
  default: phi               # Qualidade superior, ~800 ms latência
  device: cuda
  precision: fp16
  use_4bit: true             # ✅ Orin compute 8.7 suporta

phi_config:
  model_name: "microsoft/Phi-3-mini-4k-instruct"
  prompt_max_length: 256
  max_tokens: 32
  summary_max_tokens: 64
  temperature: 0.7
  top_p: 0.95
```

### DialoGPT (mais rápido)

```yaml
models:
  default: dialogpt          # Ultra-rápido ~150 ms, qualidade aceitável
  device: cuda
  precision: fp16
```

---

## 🧪 Validação

### 1. CUDA Status

```bash
python3 -c "
import torch
print(f'CUDA: {torch.cuda.is_available()}')
print(f'Version: {torch.version.cuda}')
print(f'Device: {torch.cuda.get_device_name(0)}')
print(f'Compute Capability: {torch.cuda.get_device_capability(0)}')
"
# Esperado: CUDA: True | Version: 11.4 | Compute: (8, 7)
```

### 2. Carregar Qwen

```bash
python3 -c "
from transformers import AutoTokenizer, AutoModelForCausalLM
import torch

model_path = '/home/user/models/Qwen2.5-0.5B-Instruct'
tokenizer = AutoTokenizer.from_pretrained(model_path)
model = AutoModelForCausalLM.from_pretrained(model_path).cuda()

print('✅ Qwen loaded successfully')
print(f'Model params: {model.num_parameters() / 1e6:.1f}M')
"
```

### 3. Teste da API

```bash
curl http://localhost:8000/health

# Diagnosticar imagem
curl -X POST http://localhost:8000/diagnose \
  -F "file=@data/illumination/normal/sample.jpg" \
  -F "frame_index=0"
```

---

## 📊 Performance Esperada

### Jetson Orin Nano (8GB)

| Modelo | Latência | VRAM | Status |
|---|---|---|---|
| DialoGPT | ~150 ms/frame | 500 MB | ✅ Rápido |
| Qwen 0.5B | ~300 ms/frame | 1.5 GB | ✅ Recomendado |
| Phi-3-mini | ~800 ms/frame | 8 GB | ⚠️ Lento |

**Tempo total (batch 10 frames):**
- DialoGPT: ~2.5s ✅
- Qwen: ~3.5s ✅
- Phi-3: ~8-10s (acima do target)

### Jetson AGX Orin (32GB)

| Modelo | Latência | VRAM | Status |
|---|---|---|---|
| DialoGPT | ~100 ms/frame | 500 MB | ✅ Ultrarrápido |
| Qwen 0.5B | ~250 ms/frame | 1.5 GB | ✅ Excelente |
| Phi-3-mini | ~500 ms/frame | 8 GB | ✅ Bom |

**Tempo total (batch 10 frames):**
- DialoGPT: ~2s ✅
- Qwen: ~3s ✅
- Phi-3: ~5s ✅

---

## 🛠️ Troubleshooting

### Erro: `nvidia-smi` não encontrado

Verifique JetPack:
```bash
cat /etc/nv_tegra_release | grep "CUDA"
# Deve mostrar CUDA 11.4
```

Se não tiver:
```bash
sudo apt-get install -y nvidia-jetpack
sudo reboot
```

### Erro: CUDA version mismatch

```bash
# Verificar PyTorch vs CUDA
python3 -c "import torch; print(torch.version.cuda)"

# Se falhar, reinstalar PyTorch para CUDA 11.4
pip install torch torchvision torchaudio \
  -f https://download.pytorch.org/whl/torch_stable.html
```

### Erro: Modelo não carrega (OOM)

Se Phi-3 falhar com out-of-memory:

```yaml
# Usar quantização 4-bit
models:
  use_4bit: true

# Ou reduzir batch size no YAML
inference:
  batch_size: 5  # em vez de 10
```

### Erro: `bitsandbytes` não funciona

Orin tem compute 8.7, que suporta `bitsandbytes`. Se falhar:

```bash
# Reinstalar com suporte a compute 8.7
pip install bitsandbytes --upgrade --force-reinstall
```

### Temperatura alta (>80°C)

```bash
# Monitorar
sudo tegrastats

# Reduzir frequência CPU/GPU (se necessário)
sudo jetson_clocks --show
sudo jetson_clocks --restore  # volta ao normal
```

---

## 🔄 Atualizações

```bash
cd ~/backend_tcc_mvp

# Atualizar código
git pull origin main

# Reinstalar deps
poetry install

# Rebuild Docker
docker-compose build --no-cache
docker-compose up -d
```

---

## 📈 Monitoramento

### Tegrastats (CPU, GPU, memory, temp)

```bash
sudo tegrastats
# Atualiza a cada 1 segundo
```

### Logs container

```bash
docker logs -f ar-diagnostic-mvp
```

### GPU em tempo real

```bash
watch -n 0.5 nvidia-smi
```

---

## 🔒 Segurança

### Firewall

```bash
sudo ufw allow from 192.168.0.0/16 to any port 8000
sudo ufw enable
```

### HTTPS via nginx

```bash
sudo apt-get install nginx
sudo certbot certonly --standalone -d your-domain.com
# Configurar proxy nginx...
```

---

## 📚 Referências

- [Jetson Orin Docs](https://docs.nvidia.com/jetson/jetson-orin/index.html)
- [JetPack 5.x Release Notes](https://docs.nvidia.com/jetson/jetpack/release-notes/index.html)
- [Qwen2.5 - Hugging Face](https://huggingface.co/Qwen/Qwen2.5-0.5B-Instruct)
- [Phi-3 - Hugging Face](https://huggingface.co/microsoft/Phi-3-mini-4k-instruct)
- [PyTorch Jetson Support](https://pytorch.org/get-started/locally/)

---

## ❓ FAQ

**P: Qual modelo escolher para Jetson Orin?**  
A: **Qwen 0.5B** (recomendado). Excelente qualidade + latência ~300 ms. Phi-3 é melhor mas ~800 ms.

**P: Posso rodar Qwen + Phi simultaneamente?**  
A: Não. Ambos.cuda() ocupariam ~9 GB. Escolha um ou redimensione com quantização.

**P: É necessário 4-bit quantization?**  
A: Não. Orin tem VRAM suficiente (8-32 GB). Use se quiser mais espaço para outros processos.

**P: Qual é a diferença de performance vs Legion RTX?**  
A: Qwen: Orin ~300ms vs RTX ~100ms (3x mais rápido). Mas Orin é portátil.

**P: Posso colocar Orin em uma suitcase e viajar?**  
A: Sim! Orin é mobile, não precisa de desktop. Levar fonte, ventilação, e você está pronto.
