# 🐳 Guia Prático: Testando na Jetson Nano (Docker)

## Visão Geral

Este guia mostra como rodar a API completa na **Jetson Nano** via Docker para demonstração no TCC.

### Performance Esperada
- ⏱️ Latência total por diagnóstico: **~20-30s** (muito lento)
- 💾 Memória: ~2-3GB VRAM usada
- ⚠️ **Advertência:** Nano é lento, ideal apenas para demonstração educacional

---

## PARTE 1: Setup Inicial no Nano

### 1.1 Conectar via SSH

```bash
# Do seu PC
ssh jetson

# Se primeira vez, pode pedir confirmação
# Are you sure you want to continue connecting? → yes
```

### 1.2 Verificar Hardware

```bash
# Verificar Jetson
jetson_release

# Esperado:
# - Jetson Nano (não AGX ou Orin)
# - JetPack 4.6.x
# - L4T R32.7.x
```

### 1.3 Clonar/Atualizar o Projeto

```bash
cd ~
git clone https://github.com/seu-repo/backend_tcc_mvp.git
cd backend_tcc_mvp

# Ou se já existe:
cd ~/backend_tcc_mvp
git pull origin main
```

---

## PARTE 2: Build Docker na Nano

### 2.1 Build da Imagem (DEMORA ~30-40min)

⚠️ **AVISO:** Primeira build é lenta! Café/paciência necessários.

```bash
cd ~/backend_tcc_mvp

# Build para Nano
docker build -f docker/Dockerfile.jetson-nano \
  -t ar-diagnostic-mvp:nano \
  .

# Ou com nome mais curto
docker build -f docker/Dockerfile.jetson-nano \
  -t ar-api-nano \
  .
```

**Monitorar progresso:**
```bash
# Em outro terminal
docker images | grep ar

# Ou acompanhar build em tempo real (em outro terminal)
dmesg -w
```

### 2.2 Verificar Build

```bash
docker images | grep ar-diagnostic

# Esperado:
# ar-diagnostic-mvp   nano    XXXXXXX    X hours ago    3.2GB
```

---

## PARTE 3: Rodar a API

### Opção A: Docker Run (Simples)

```bash
cd ~/backend_tcc_mvp

docker run -it --rm \
  --gpus all \
  --name ar-api-nano \
  -p 8000:8000 \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/models/cache:/app/models/cache \
  -v $(pwd)/logs:/app/logs \
  -e TRANSFORMERS_CACHE=/app/models/cache \
  -e AR_CONFIG_FILE=/app/app/config/thresholds.jetson.yaml \
  ar-diagnostic-mvp:nano \
  poetry run ar-api
```

**Esperado:**
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete
```

---

### Opção B: Docker Compose (Recomendado)

```bash
cd ~/backend_tcc_mvp

# Subir em background
docker compose -f docker-compose-nano.yml up -d

# Ver logs
docker compose -f docker-compose-nano.yml logs -f

# Ver container rodando
docker ps | grep nano
```

**Para parar:**
```bash
docker compose -f docker-compose-nano.yml down
```

---

## PARTE 4: Testar a API

### 4.1 Verificar API Respondendo

```bash
# Do Nano, testar localmente
curl http://localhost:8000/health

# Esperado:
# {"status":"ok"}
```

### 4.2 Acessar API do PC (via SSH)

```bash
# Do seu PC (fora do Nano)
curl http://jetson:8000/health

# Ou via IP
# Descobrir IP do Nano:
ssh jetson "hostname -I"

curl http://192.168.X.X:8000/health
```

### 4.3 Ver Documentação Swagger

```bash
# Abrir no navegador do seu PC:
http://jetson:8000/docs

# Ou via IP:
http://192.168.X.X:8000/docs
```

### 4.4 Fazer Teste Simples

```bash
# 1. Prepare os arquivos
ssh jetson "ls ~/backend_tcc_mvp/data/illumination/normal/"

# 2. Envie para testar via curl
curl -X POST "http://jetson:8000/api/v1/diagnose" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "qwen",
    "batch_size": 1,
    "images_paths": ["/app/data/illumination/normal/sample1.jpg"]
  }'
```

### 4.5 Rodar Teste Completo

```bash
# Dentro do container ou via ssh
ssh jetson "cd ~/backend_tcc_mvp && docker exec ar-api-nano \
  poetry run python tests/test_api_quick.py"
```

---

## PARTE 5: Monitorar Performance

### 5.1 Monitorar VRAM em Tempo Real

```bash
# Em um terminal separado no Nano
watch -n 1 "free -h && echo '---' && nvidia-smi"

# Ou com tegrastats (MÃO especial Jetson)
sudo tegrastats

# Tecla 'q' para sair
```

### 5.2 Ver Logs da API

```bash
# Opção 1: Ao vivo (docker run)
# Já mostra na tela se usou -it

# Opção 2: Docker compose
docker compose -f docker-compose-nano.yml logs -f ar-diagnostic-mvp-nano

# Opção 3: Via SSH
ssh jetson "docker logs ar-api-nano -f"
```

---

## PARTE 6: Conectar Frontend

### 6.1 Se Tem Frontend Web

**Configure a URL da API no frontend:**

```javascript
// src/config.js (ou similar)
export const API_URL = 'http://jetson:8000';
// ou
export const API_URL = 'http://192.168.X.X:8000';
```

**Ou variável ambiente:**
```bash
export REACT_APP_API_URL=http://jetson:8000
npm start
```

### 6.2 Testar Conexão

```bash
# Do browser:
# 1. Abra http://jetson:8000/docs (API Swagger)
# 2. Clique em "Try it out"
# 3. Envie uma requisição
```

---

## PARTE 7: Troubleshooting

### ❌ "Docker: command not found"
```bash
# Docker não instalado no Nano
ssh jetson "which docker"
# Se vazio:
ssh jetson "sudo apt update && sudo apt install -y docker.io"
```

### ❌ "Build falhou com erro de memória"
```bash
# Aumentar swap (Nano tem pouca RAM)
ssh jetson "free -h"  # Ver memória disponível

# Se < 2GB, aumentar swap:
ssh jetson "
  sudo fallocate -l 4G /var/swapfile
  sudo chmod 600 /var/swapfile
  sudo mkswap /var/swapfile
  sudo swapon /var/swapfile
"

# Tentar build novamente
```

### ❌ "CUDA returned an error code"
```bash
# PyTorch não vê CUDA
ssh jetson "nvidia-smi"

# If não funciona, reinicie Nano
ssh jetson "sudo reboot"

# Depois reconstruir:
docker build -f docker/Dockerfile.jetson-nano \
  --no-cache \
  -t ar-diagnostic-mvp:nano \
  .
```

### ❌ "Connection refused" ao acessar API
```bash
# Verificar se container está rodando
docker ps | grep ar-api-nano

# Se não está, ver logs
docker logs ar-api-nano

# Reiniciar:
docker stop ar-api-nano
docker rm ar-api-nano

# Resubir
docker run ... (comandos acima)
```

### ❌ "Out of memory" ao processar imagem
```bash
# Reduzir batch size em app/config/thresholds.jetson.yaml:
# batch_size: 1  (em vez de 2 ou 4)

# Ou desabilitar FP16
docker run ... \
  -e MODEL_PRECISION=fp32 \
  ...
```

---

## PARTE 8: Script de Automatização

Salve como `run-nano.sh` no seu PC:

```bash
#!/bin/bash

# Script para rodar API no Nano automaticamente

NANO_HOST="jetson"
NANO_USER="jetson"
PROJECT_PATH="~/backend_tcc_mvp"

echo "🚀 Iniciando API no Nano..."

ssh ${NANO_HOST} "
  cd ${PROJECT_PATH}

  echo '[1/3] Verificando build...'
  docker images | grep 'ar-diagnostic-mvp.*nano' > /dev/null || {
    echo '[2/3] Build não existe. Construindo...'
    docker build -f docker/Dockerfile.jetson-nano \
      -t ar-diagnostic-mvp:nano .
  }

  echo '[3/3] Subindo container...'
  docker compose -f docker-compose-nano.yml down 2>/dev/null
  docker compose -f docker-compose-nano.yml up
"
```

**Uso:**
```bash
chmod +x run-nano.sh
./run-nano.sh
```

---

## PARTE 9: Benchmark Esperado (TCC)

Para apresentar no TCC, espere:

### Métricas após setup bem-sucedido

```
┌──────────────────────────────────────────┐
│ JETSON NANO - Performance Esperada        │
├──────────────────────────────────────────┤
│ Latência total/imagem:    ~20-30s        │
│ FPS (frames/second):      0.03-0.05      │
│ Memória usada:            ~2,500MB       │
│ Temperatura GPU:          45-60°C        │
│ Modelo suportado:         Qwen 0.5B      │
│ Quantização:              4-bit (INT4)   │
│ Acurácia:                 ~95-98%        │
└──────────────────────────────────────────┘
```

**Como capturar para o TCC:**

```bash
# 1. Tirar screenshot do Swagger
# http://jetson:8000/docs

# 2. Fazer requisição e capturar resposta
curl http://jetson:8000/api/v1/diagnose \
  -H "Content-Type: application/json" \
  -d '...' | tee resultado.json

# 3. Monitorar com tegrastats
sudo tegrastats > nano_metrics.txt &
# (deixa rodando enquanto processa)
kill %1  # parar ao fim

# 4. Ver logs
docker logs ar-api-nano > api_logs.txt
```

---

## PARTE 10: Checklist Final

Antes de apresentar no TCC:

- [ ] Docker build completou sem erros
- [ ] Container sobe sem crash
- [ ] API responde em `http://jetson:8000/health`
- [ ] Swagger acessível em `http://jetson:8000/docs`
- [ ] Teste simples executa
- [ ] Logs não mostram erros CUDA
- [ ] VRAM não fica em 100% constantemente
- [ ] Latência está entre 20-30s (como esperado)
- [ ] Podem conectar do PC via `ssh jetson`
- [ ] Screenshots e logs salvos para apresentação

---

## 📞 Referências Rápidas

### Comandos Docker Essenciais

| Comando | O que faz |
|---------|----------|
| `docker build -f docker/Dockerfile.jetson-nano -t ar-diagnostic-mvp:nano .` | Build imagem |
| `docker ps` | Ver containers rodando |
| `docker logs [container]` | Ver logs |
| `docker stop [container]` | Parar container |
| `docker rm [container]` | Deletar container |
| `docker compose -f docker-compose-nano.yml up -d` | Subir em background |
| `docker compose -f docker-compose-nano.yml down` | Parar tudo |

### Comandos SSH Úteis

| Comando | O que faz |
|---------|----------|
| `ssh jetson` | Conectar |
| `ssh jetson "ls ~/backend_tcc_mvp"` | Comando remoto |
| `scp arquivo.txt jetson:~` | Enviar arquivo |
| `scp jetson:~/arquivo.txt .` | Baixar arquivo |

### URLs da API

| URL | Descrição |
|-----|-----------|
| `http://jetson:8000/health` | Health check |
| `http://jetson:8000/docs` | Swagger UI |
| `http://jetson:8000/redoc` | ReDoc |
| `http://jetson:8000/api/v1/diagnose` | Endpoint principal |

---

## ⏱️ Timeline Estimado

| Etapa | Tempo | Notas |
|-------|-------|-------|
| Clone do repo | 2 min | Rápido |
| Docker build | 30-40 min | ☕ Café aqui |
| Rodar API | 1 min | Após build |
| Primeiro teste | 30 seg | Rápido |
| Teste completo (imagem) | 30 sec | Lento no Nano |

**Total: ~45-50 min de espera (mostly build)**

---

## 💡 Dicas pro TCC

1. **Rode tudo antes da apresentação** — não confie em estar "pronto no dia"
2. **Tenha um Nano ligado durante toda a apresentação** — desligue só ao fim
3. **Capture screenshots** de Swagger e resposta da API com sucesso
4. **Mostre os logs** provando que processou corretamente
5. **Compare Orin vs Nano** — mostra diferença crítica
6. **Tenha plano B** se Nano travar (mostrar vídeo pré-gravado ou Orin)

---

**Última atualização:** 2026-04-10
