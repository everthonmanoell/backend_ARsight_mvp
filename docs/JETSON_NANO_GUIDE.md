# Jetson Nano Setup & Deployment Guide

Guia completo para setup e deploy do AR Diagnostic MVP no **Jetson Nano** com **JetPack 4.6** (L4T R32.7).

> ⚠️ **Nota:** Jetson Nano suporta apenas **DialoGPT-small** com performance adequada. Ver [MODEL_SELECTION.md](MODEL_SELECTION.md) para comparação de modelos.

## ✅ Hardware Verificado

| Item | Versão | Status |
|---|---|---|
| **Jetson Nano** | Tegra X1 (4GB) | ✅ Testado |
| **JetPack** | 4.6.x | ✅ Testado |
| **L4T** | R32.7.x | ✅ Testado |
| **CUDA** | 10.2 | ✅ Funciona |
| **GPU Compute** | 5.3 (Maxwell) | ✅ Compatível |
| **PyTorch** | 1.10.0 | ✅ Instável |

---

## 📋 Pré-requisitos

### 1. Verificar JetPack
```bash
sudo apt-cache show nvidia-jetpack | grep "^Version" | head -1
# Esperado: Version: 4.6.x-bXX
```

### 2. Docker + NVIDIA Runtime
```bash
# Instala Docker
sudo apt-get update
sudo apt-get install -y docker.io

# Adiciona usuário ao grupo
sudo usermod -aG docker $USER
newgrp docker

# Instala NVIDIA Container Runtime
sudo apt-get install -y nvidia-container-runtime

# Configura Docker daemon
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

# Testa GPU no Docker
docker run --rm --runtime=nvidia nvcr.io/nvidia/l4t-base:r32.7.1 nvidia-smi
```

### 3. Python 3.6 (já vem instalado)
```bash
python3 --version  # Deve ser 3.6.9
```

### 4. Poetry (opcional, alternativa ao pip)
```bash
curl -sSL https://install.python-poetry.org | python3 -
export PATH="$HOME/.local/bin:$PATH"
poetry --version
```

---

## 🚀 Setup Local (Recomendado para Desenvolvimento)

### Opção A: Com Poetry

```bash
cd ~/backend_tcc_mvp

# Usar configuração Jetson Nano
cp pyproject-jetson-nano.toml pyproject.toml

# Criar venv e instalar
poetry env use python3
poetry install

# Rodar
poetry run ar-api
```

### Opção B: Com pip simples

```bash
cd ~/backend_tcc_mvp

# Instalar dependências
pip install -r requirements-jetson.txt

# Rodar (PyTorch já deve estar instalado via imagem base JetPack)
python3 -m uvicorn app.api.main:app --host 0.0.0.0 --port 8000
```

---

## 🐳 Setup Docker (Recomendado para Produção)

### Build

```bash
cd ~/backend_tcc_mvp

# Build específico para Nano
docker build -f docker/Dockerfile.jetson-nano \
  -t ar-diagnostic-mvp:jetson-nano .

# Tempo de build: ~5-10 min (primeira vez: download ~2GB)
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
  ar-diagnostic-mvp:jetson-nano
```

### Ou com Docker Compose

```bash
# Editar docker-compose.yml se necessário
docker-compose -f docker-compose-nano.yml up -d

# Logs
docker-compose -f docker-compose-nano.yml logs -f

# Parar
docker-compose -f docker-compose-nano.yml down
```

---

## ⚙️ Configuração (YAML)

O `app/config/thresholds.yaml` já está otimizado para Jetson Nano:

```yaml
models:
  default: dialogpt           # ✅ Único modelo viável
  device: cuda                # ✅ Usar GPU
  precision: fp16             # ✅ Reduz memória
  use_4bit: false             # ❌ NUNCA habilitar (Maxwell não suporta)

dialogpt_config:
  model_name: "microsoft/DialoGPT-small"
  prompt_max_length: 256      # Reduzido de 512 para performance
  max_tokens: 20              # Per-frame
  summary_max_tokens: 32
  temperature: 0.3
  top_p: 0.85
  greedy_decoding: true       # Determinístico
```

> **Nunca mude para `use_4bit: true` ou `default: qwen`.** O Nano não tem VRAM para isso.

---

## 🧪 Validação

### 1. Verificar CUDA
```bash
python3 -c "import torch; print(f'CUDA: {torch.cuda.is_available()}'); print(f'Version: {torch.version.cuda}')"
# Esperado: CUDA: True  |  Version: 10.2
```

### 2. Health Check
```bash
curl http://localhost:8000/health
# Esperado: {"status":"healthy"}
```

### 3. Teste com Imagem
```bash
# Preparar imagem de teste
cp data/illumination/normal/sample.jpg /tmp/test.jpg

# Enviar para diagnóstico
curl -X POST http://localhost:8000/diagnose \
  -F "file=@/tmp/test.jpg" \
  -F "frame_index=0"

# Esperado: JSON com diagnosis
```

---

## 📊 Performance Esperada

**Jetson Nano com DialoGPT-small:**

| Métrica | Valor | Status |
|---|---|---|
| PDI (rule engine) | ~91 ms/frame | ✅ Rápido |
| DialoGPT inference | ~250 ms/frame | ✅ Aceitável |
| **Total (batch 10)** | **~3.4 s** | ✅ Target met |
| VRAM usado | ~2.2 GB | ✅ Confortável |
| FPS | ~3 frames/s | ✅ Contínuo |

---

## 🛠️ Troubleshooting

### Erro: `nvidia-smi` não encontrado no container

```bash
# Verificar se runtime está configurado
docker info | grep -i runtime
# Deve listar: Runtimes: nvidia runc

# Reconfigurar se necessário
sudo apt-get install --reinstall nvidia-container-runtime
sudo systemctl restart docker
```

### Erro: `CUDA out of memory`

O Nano tem memória compartilhada. Libere processos:

```bash
# Ver uso de memória
sudo tegrastats

# Parar serviços pesados
sudo systemctl stop lightdm  # se usar GUI
```

### Erro: `ModuleNotFoundError: No module named 'torch'`

```bash
# Confirmar PyTorch instalado
python3 -c "import torch; print(torch.__version__)"

# Se falhar, reinstalar via pip
pip install --upgrade \
  https://nvidia.box.com/shared/static/p57jwntjetr23c7d647vsd20tkgp4b3a.whl
```

### Erro: `bitsandbytes` ou quantização falha

**Não use quantização no Nano!** Maxwell (compute 5.3) não é suportado.

```yaml
# CORRETO:
models:
  use_4bit: false

# ERRADO (não funciona no Nano):
models:
  use_4bit: true
```

### Erro: `Permission denied` no Docker

```bash
sudo usermod -aG docker $USER
newgrp docker
docker run hello-world  # Verificar permissão
```

---

## 🔄 Atualizações

```bash
cd ~/backend_tcc_mvp

# Atualizar código
git pull origin main

# Se usar Poetry
poetry install

# Se usar Docker
docker-compose -f docker-compose-nano.yml build --no-cache
docker-compose -f docker-compose-nano.yml up -d
```

---

## 📈 Monitoramento

### Recursos em tempo real

```bash
# Stats da Jetson (CPU, GPU, memory, temperature)
sudo tegrastats

# Logs do container
docker logs -f ar-diagnostic-mvp

# Uso de memória
docker stats ar-diagnostic-mvp
```

### Verificar GPU em uso

```bash
# Enquanto roda o serviço, em outro terminal:
watch -n 1 nvidia-smi
# Deve mostrar ~2-2.5 GB de GPU memory usado
```

---

## 🔒 Segurança (Produção)

### Firewall local

```bash
# Permite apenas rede local (192.168.x.x)
sudo ufw allow from 192.168.0.0/16 to any port 8000
sudo ufw enable
```

### HTTPS (opcional)

```bash
# Usar nginx reverse proxy com SSL
sudo apt-get install nginx

# Configurar certificado Let's Encrypt
sudo apt-get install certbot python3-certbot-nginx
sudo certbot certonly --standalone -d your-domain.com
```

---

## 📚 Referências

- [NVIDIA Jetson Nano Docs](https://docs.nvidia.com/jetson/jetson-nano/index.html)
- [DialoGPT - Hugging Face](https://huggingface.co/microsoft/DialoGPT-small)
- [JetPack 4.6 Release Notes](https://docs.nvidia.com/jetson/jetpack/release-notes/index.html)
- [L4T Documentation](https://docs.nvidia.com/jetson/l4t-multimedia/index.html)
- [NVIDIA Container Toolkit](https://github.com/NVIDIA/nvidia-docker)

---

## ❓ FAQ

**P: Posso rodar Qwen no Jetson Nano?**  
A: Não. Qwen 0.5B ocupa ~1 GB, deixando pouco para a aplicação. DialoGPT é mais rápido (250 ms vs 500 ms).

**P: E Phi-3?**  
A: Phi-3-mini ocupa 7.6 GB — não cabe nos 4 GB do Nano.

**P: Posso usar quantização 4-bit?**  
A: Não. `bitsandbytes` requer GPU compute ≥ 7.5 (Turing+). Nano tem Maxwell (5.3).

**P: Qual é o máximo de fps?**  
A: ~3 fps contínuos (batch de 10 images em 3.4s).

**P: Posso rodar em CPU mantendo GPU disponível?**  
A: Sim, configurar `device: cpu` no YAML, mas será ~5x mais lento.

**P: Como monitorar a temperatura?**  
A: `sudo tegrastats` mostra temp em tempo real. Preocupe-se se passar 80°C.
