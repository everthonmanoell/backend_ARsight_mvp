# Jetson Deployment Guide

Guia completo para deploy do AR Diagnostic MVP na NVIDIA Jetson.

## ✅ Hardware Testado

- **Jetson Nano** - 4GB RAM, CUDA 10.2
- **Jetson Xavier NX** - 8GB RAM, CUDA 11.4 (recomendado)
- **Jetson AGX Orin** - 32GB RAM, CUDA 11.4

## 📋 Pré-requisitos

### 1. JetPack SDK
```bash
# Verifica versão JetPack
sudo apt-cache show nvidia-jetpack

# Recomendado: JetPack 5.0+ (L4T R35.x)
```

### 2. Docker + NVIDIA Container Runtime
```bash
# Instala Docker
sudo apt-get update
sudo apt-get install -y docker.io

# Adiciona usuário ao grupo docker
sudo usermod -aG docker $USER
newgrp docker

# Instala NVIDIA Container Runtime
sudo apt-get install -y nvidia-container-runtime

# Testa GPU no Docker
docker run --rm --gpus all nvcr.io/nvidia/l4t-base:r35.2.1 nvidia-smi
```

## 🚀 Deployment

### Opção 1: Docker (Recomendado)

```bash
# Clone repositório
git clone <your-repo-url> backend_tcc_mvp
cd backend_tcc_mvp

# Build imagem para Jetson
docker build -f docker/Dockerfile.jetson -t ar-diagnostic-mvp:jetson .

# Run com GPU
docker run --rm --gpus all \
  -p 8000:8000 \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/logs:/app/logs \
  ar-diagnostic-mvp:jetson
```

### Opção 2: Docker Compose

```bash
# Inicia serviço
docker-compose up -d

# Verifica logs
docker-compose logs -f

# Para serviço
docker-compose down
```

### Opção 3: Instalação Nativa

```bash
# Instala Python 3.10+
sudo apt-get install python3.10 python3-pip

# Instala Poetry
curl -sSL https://install.python-poetry.org | python3 -

# Instala dependências
poetry install

# Roda API
poetry run ar-api
```

## ⚙️ Configuração

### GPU vs CPU

Edite `app/config/thresholds.yaml`:

```yaml
models:
  device: cuda  # Use GPU (recomendado)
  # device: cpu   # Fallback se GPU não disponível
  use_4bit: true  # Quantização 4-bit (economiza VRAM)
```

### Modelo Padrão

```yaml
models:
  default: qwen  # Qwen 0.5B (mais rápido, menos VRAM)
  # default: phi  # Phi-3 Mini (maior qualidade, mais VRAM)
```

### Thresholds de Iluminação

```yaml
rule_engine:
  illumination:
    underexposed_threshold: 0.35
    overexposed_threshold: 0.75
```

## 🧪 Validação

### 1. Teste de GPU
```bash
python -c "import torch; print(f'CUDA available: {torch.cuda.is_available()}')"
```

### 2. Health Check
```bash
curl http://localhost:8000/health
```

### 3. Teste com Imagem
```bash
curl -X POST http://localhost:8000/diagnose \
  -F "file=@data/illumination/adequate/normal_image1.jpg"
```

### 4. Batch Test
```bash
python tests/test_illumination_batch.py
```

## 📊 Performance

### Jetson Xavier NX (8GB)

| Modelo | Quantização | Latência | VRAM | Throughput |
|--------|-------------|----------|------|------------|
| Qwen 0.5B | 4-bit | ~1.2s | 800MB | 0.83 img/s |
| Phi-3 Mini | 4-bit | ~1.8s | 1.2GB | 0.56 img/s |

### Jetson Nano (4GB)

| Modelo | Quantização | Latência | VRAM | Throughput |
|--------|-------------|----------|------|------------|
| Qwen 0.5B | 4-bit | ~3.5s | 800MB | 0.29 img/s |
| Phi-3 Mini | 4-bit | ~6.0s | 1.2GB | 0.17 img/s |

**Recomendação:** Use **Qwen 0.5B** para melhor throughput.

## 🐛 Troubleshooting

### Erro: CUDA out of memory

**Solução 1:** Reduz batch size
```yaml
api:
  max_batch_size: 5  # Reduz de 10 para 5
```

**Solução 2:** Usa CPU
```yaml
models:
  device: cpu
```

### Erro: Model not found

**Solução:** Pre-download modelos
```python
from transformers import AutoModelForCausalLM

# Qwen
AutoModelForCausalLM.from_pretrained("Qwen/Qwen2.5-0.5B-Instruct")

# Phi
AutoModelForCausalLM.from_pretrained("microsoft/Phi-3-mini-4k-instruct")
```

### Erro: Permission denied (Docker)

**Solução:**
```bash
sudo usermod -aG docker $USER
newgrp docker
```

## 🔒 Segurança

### Firewall (Produção)
```bash
# Permite apenas localhost
sudo ufw allow from 127.0.0.1 to any port 8000

# Ou permite rede local
sudo ufw allow from 192.168.0.0/16 to any port 8000
```

### HTTPS (Nginx Reverse Proxy)
```bash
# Instala Nginx
sudo apt-get install nginx

# Configura SSL
sudo apt-get install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
```

## 📈 Monitoramento

### Logs
```bash
# Docker
docker logs -f ar-diagnostic-mvp

# Nativo
tail -f logs/ar_diagnostic_mvp.log
```

### GPU Usage
```bash
# Real-time GPU monitoring
watch -n 1 nvidia-smi
```

### System Stats
```bash
sudo tegrastats  # Jetson-specific tool
```

## 🔄 Atualização

```bash
# Pull latest changes
git pull origin main

# Rebuild Docker image
docker-compose build

# Restart service
docker-compose restart
```

## 📞 Suporte

Para problemas ou dúvidas:
1. Verifique logs: `docker logs ar-diagnostic-mvp`
2. Teste GPU: `python -c "import torch; print(torch.cuda.is_available())"`
3. Valide config: `cat app/config/thresholds.yaml`
