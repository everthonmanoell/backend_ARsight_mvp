# Jetson Deployment Guide

Guia completo para deploy do AR Diagnostic MVP na NVIDIA Jetson.

## ✅ Hardware Suportado

| Hardware | RAM | JetPack | L4T | CUDA | Status |
|---|---|---|---|---|---|
| **Jetson Nano** | 4GB | **4.6.x** (L4T R32.7.x) | R32.7 | 10.2 | ✅ Testado |
| Jetson Xavier NX | 8GB | 5.0+ (L4T R35.x) | R35 | 11.4 | Compatível |
| Jetson AGX Orin | 32GB | 5.0+ (L4T R35.x) | R35 | 11.4 | Compatível |

> **⚠️ Importante:** JetPack 5.x **não existe** para o Jetson Nano. O Nano usa exclusivamente JetPack 4.6.x.

## ⚠️ Limitações do Jetson Nano (JetPack 4.6)

| Limitação | Detalhe |
|---|---|
| **Sem quantização 4-bit** | `bitsandbytes` requer GPU compute ≥ 7.5 (Turing+). Nano = Maxwell (compute **5.3**). |
| **Apenas modelo Qwen** | Phi-3 Mini (3.8B params) ocupa ~7.6 GB em fp16 — não cabe nos 4 GB do Nano. Qwen 0.5B ocupa ~1 GB em fp16. |
| **Python 3.8** | Ubuntu 18.04 do L4T tem Python 3.6 por padrão. O projeto requer 3.8+ (instalado pelo Dockerfile). |
| **PyTorch 1.10** | Versão máxima disponível via wheel oficial NVIDIA para CUDA 10.2 / aarch64. |

## 📋 Pré-requisitos

### 1. Verificar JetPack instalado
```bash
sudo apt-cache show nvidia-jetpack | grep "^Version" | head -1
# Esperado: Version: 4.6.x-bXX
```

### 2. Docker + NVIDIA Container Runtime
```bash
# Instala Docker
sudo apt-get update
sudo apt-get install -y docker.io

# Adiciona usuário ao grupo docker
sudo usermod -aG docker $USER
newgrp docker

# Instala NVIDIA Container Runtime (JetPack 4.6 usa nvidia-container-runtime, não toolkit)
sudo apt-get install -y nvidia-container-runtime

# Configura Docker para usar o runtime NVIDIA por padrão
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

# Testa GPU no Docker — use a tag r32.7.1 (não r35.x, que não existe no Nano)
docker run --rm --runtime=nvidia nvcr.io/nvidia/l4t-base:r32.7.1 nvidia-smi
```

## 🖥️ Transferindo o projeto para a Jetson

Você **precisa** ter o código na Jetson. Escolha uma opção:

### Opção A: Git Clone (recomendado)
```bash
# Na Jetson
git clone <seu-repo-url> backend_tcc_mvp
cd backend_tcc_mvp
```

### Opção B: SCP do desktop para a Jetson
```bash
# No desktop (substitua <jetson-ip> pelo IP da sua Jetson)
scp -r /caminho/para/backend_tcc_mvp das9@<jetson-ip>:~/backend_tcc_mvp
```

### Opção C: rsync (sincronização incremental)
```bash
# No desktop
rsync -avz --exclude='__pycache__' --exclude='*.pyc' \
  /caminho/para/backend_tcc_mvp/ das9@<jetson-ip>:~/backend_tcc_mvp/
```

## 🚀 Deployment

### Opção 1: Docker Compose (Recomendado)

```bash
# Na Jetson, dentro da pasta do projeto
cd ~/backend_tcc_mvp

# Build — a primeira vez leva vários minutos (download da imagem base ~2GB)
docker-compose build

# Inicia serviço
docker-compose up -d

# Verifica logs
docker-compose logs -f

# Para serviço
docker-compose down
```

### Opção 2: Docker direto

```bash
# Build imagem para Jetson Nano
docker build -f docker/Dockerfile.jetson -t ar-diagnostic-mvp:jetson-nano .

# Run com GPU via nvidia-container-runtime
docker run --rm \
  --runtime=nvidia \
  -e NVIDIA_VISIBLE_DEVICES=all \
  -p 8000:8000 \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/logs:/app/logs \
  ar-diagnostic-mvp:jetson-nano
```

### Opção 3: Instalação Nativa

```bash
# Python 3.8 (Ubuntu 18.04)
sudo apt-get install python3.8 python3.8-dev python3.8-distutils python3-pip

# PyTorch 1.10 para Jetson Nano (wheel oficial NVIDIA — CUDA 10.2, aarch64, Python 3.8)
# Referência: https://forums.developer.nvidia.com/t/pytorch-for-jetson/72048
python3.8 -m pip install \
  https://developer.download.nvidia.com/compute/redist/jp/v461/pytorch/torch-1.10.0a0+git36449ea-cp38-cp38-linux_aarch64.whl

# Dependências da aplicação (sem torch/bitsandbytes)
python3.8 -m pip install -r requirements-jetson.txt

# Roda API
python3.8 -m uvicorn app.api.main:app --host 0.0.0.0 --port 8000
```

## ⚙️ Configuração (já ajustada para o Nano)

O `app/config/thresholds.yaml` já está configurado corretamente para o Jetson Nano:

```yaml
models:
  default: qwen       # Único modelo viável no Nano (0.5B params, ~1 GB fp16)
  device: cuda        # Usa GPU
  use_4bit: false     # DESABILITADO — Maxwell (compute 5.3) não suporta bitsandbytes
```

> **Nunca habilite `use_4bit: true` no Nano.** O `bitsandbytes` travará na inicialização.

## 🧪 Validação

### 1. Teste de GPU
```bash
python3.8 -c "import torch; print('CUDA disponível:', torch.cuda.is_available()); print('Versão CUDA:', torch.version.cuda)"
# Esperado: CUDA disponível: True  |  Versão CUDA: 10.2
```

### 2. Health Check
```bash
curl http://localhost:8000/health
```

### 3. Teste com Imagem
```bash
curl -X POST http://localhost:8000/diagnose \
  -F "file=@data/illumination/normal/normal_image1.jpg"
```

## 📊 Performance Esperada — Jetson Nano (4GB, JetPack 4.6)

| Modelo | Quantização | VRAM | Latência estimada |
|--------|-------------|------|-------------------|
| **Qwen 0.5B** | fp16 (sem 4-bit) | ~1 GB | ~4–6 s |
| Phi-3 Mini | — | **não cabe** | ❌ |

> A latência é maior que a documentada anteriormente (que assumia 4-bit em hardware mais novo).

## 🐛 Troubleshooting

### Erro: `nvidia-smi` não encontrado dentro do container
```bash
# Verifique se o runtime NVIDIA está configurado
docker info | grep -i runtime
# Deve listar: Runtimes: nvidia runc
```

### Erro: `Error response from daemon: Unknown runtime specified nvidia`
```bash
# Reinstale e reconfigure o runtime
sudo apt-get install --reinstall nvidia-container-runtime
sudo systemctl restart docker
```

### Erro: `bitsandbytes` / `CUDA Setup failed`
O `bitsandbytes` **não é compatível** com o Jetson Nano. Verifique:
```yaml
# app/config/thresholds.yaml
models:
  use_4bit: false   # Deve ser false
```

### Erro: `CUDA out of memory`
O Nano tem memória compartilhada (CPU+GPU). Libere processos:
```bash
# Verifica o que está usando memória
sudo tegrastats
# Mata processos pesados se necessário
sudo systemctl stop <serviço-pesado>
```

### Erro: `ModuleNotFoundError: No module named 'torch'`
```bash
# Confirma versão Python usada
python3.8 -c "import torch; print(torch.__version__)"
# Se falhar, reinstale o wheel
python3.8 -m pip install \
  https://developer.download.nvidia.com/compute/redist/jp/v461/pytorch/torch-1.10.0a0+git36449ea-cp38-cp38-linux_aarch64.whl
```

### Erro: `Permission denied` (Docker)
```bash
sudo usermod -aG docker $USER
newgrp docker
```

## 🔒 Segurança

### Firewall
```bash
# Permite apenas rede local
sudo ufw allow from 192.168.0.0/16 to any port 8000
sudo ufw enable
```

## 📈 Monitoramento

```bash
# Stats em tempo real da Jetson (CPU, GPU, RAM, temperatura)
sudo tegrastats

# Logs do container
docker logs -f ar-diagnostic-mvp

# Uso de memória do modelo
docker stats ar-diagnostic-mvp
```

## 🔄 Atualização

```bash
# Na Jetson
cd ~/backend_tcc_mvp
git pull origin main

# Rebuild e restart
docker-compose build
docker-compose restart
```
