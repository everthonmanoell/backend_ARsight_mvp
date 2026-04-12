# 🚀 Jetson Nano - Guia Completo (One-Stop Reference)

**Seu manual único para rodar a API na Jetson Nano** — sem precisar de outros arquivos!

---

## 📋 Índice Rápido
- [Conectar](#conectar)
- [Build Docker](#build-docker)
- [Rodar API](#rodar-api)
- [Testar](#testar)
- [Monitorar](#monitorar)
- [Troubleshooting](#troubleshooting)
- [Dicas TCC](#dicas-tcc)
- [Checklist](#checklist)

---

## 🔌 Conectar

```bash
# Do seu PC
ssh jetson

# Se é primeira vez, confirme com 'yes'
```

**Esperado:** Você está no Nano (`jetson-nano:~$`)

---

## 🏗️ Build Docker

⏱️ **Primeira vez: 30-40 minutos** ☕

```bash
cd ~/backend_tcc_mvp
docker build -f docker/Dockerfile.jetson-nano -t ar-diagnostic-mvp:nano .
```

**Monitorar a partir de outro terminal:**
```bash
ssh jetson "docker images | grep ar-diagnostic"
```

**Quando terminar, verá:**
```
ar-diagnostic-mvp   nano   SHA   40 minutes ago   3.2GB
```

✅ Build completo!

---

## 🚀 Rodar API

### Opção 1: Docker Compose (Simples)

```bash
cd ~/backend_tcc_mvp

# Parar se existir anteriormente
docker-compose down

# Subir
docker-compose up -d

# Ver status
docker ps
```

**Esperado:**
```
ar-diagnostic-mvp   Up 2 minutes   0.0.0.0:8000->8000/tcp
```

### Opção 2: Docker Direto (Se docker-compose falhar)

```bash
docker run -d \
  --gpus all \
  --name ar-api-nano \
  -p 8000:8000 \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/models/cache:/app/models/cache \
  -e TRANSFORMERS_CACHE=/app/models/cache \
  -e AR_CONFIG_FILE=/app/app/config/thresholds.jetson.yaml \
  ar-diagnostic-mvp:nano \
  poetry run ar-api
```

✅ API rodando!

---

## 🧪 Testar

### Ver Logs

```bash
# Opção 1 (melhor)
docker logs -f ar-diagnostic-mvp

# Opção 2
docker-compose logs -f

# Sair: Ctrl+C
```

**Esperado:**
```
...
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete
```

### Health Check (do seu PC em novo terminal)

```bash
curl http://jetson:8000/health
```

**Esperado:**
```json
{"status":"ok"}
```

### Ver Documentação Swagger

Abra no navegador:
```
http://jetson:8000/docs
```

### Fazer Requisição via Swagger

1. Abra `http://jetson:8000/docs`
2. Clique em `/api/v1/diagnose`
3. Clique "Try it out"
4. Clique "Execute"
5. Aguarde ~25 segundos (Nano é lento!)
6. Veja resultado

---

## 📊 Monitorar Performance

**Em terminal separado no Nano:**

```bash
# Opção 1: Monitorar continuum
watch -n 1 'free -h && echo "---" && nvidia-smi'

# Opção 2: Especial Jetson (MÃO melhor)
sudo tegrastats

# Sair: Ctrl+C
```

**Esperado ao processar:**
```
MemUse=2100/3964MB   (GPUFreq 729MHz@80°C)
```

---

## 🛑 Parar API

```bash
# Opção 1: Docker Compose
docker-compose down

# Opção 2: Docker direto
docker stop ar-diagnostic-mvp
docker rm ar-diagnostic-mvp

# Verificar
docker ps
```

---

## 🆘 Troubleshooting

### ❌ "docker compose logs -f" não funciona

**Causa:** Nano tem Docker antigo (sem `docker compose` novo)  
**Solução:**
```bash
# Use isto em vez disso:
docker logs -f ar-diagnostic-mvp
```

### ❌ "CUDA returned an error code"

```bash
# Reiniciar Nano
sudo reboot

# Aguarde 2 min, reconecte:
ssh jetson

# Tentar subir novamente
```

### ❌ "Build falhou com erro de memória"

```bash
# Aumentar swap
sudo fallocate -l 4G /var/swapfile
sudo chmod 600 /var/swapfile
sudo mkswap /var/swapfile
sudo swapon /var/swapfile

# Tentar build novamente (com cache limpo)
docker system prune -f --all
docker build --no-cache -f docker/Dockerfile.jetson-nano -t ar-diagnostic-mvp:nano .
```

### ❌ API respondendo muito lentamente ou errando

```bash
# Ver logs detalhados
docker logs ar-diagnostic-mvp

# Se erro CUDA, reinstalar torch
docker exec ar-diagnostic-mvp poetry run pip install --force-reinstall torch==1.10.0

# Reiniciar container
docker restart ar-diagnostic-mvp
```

### ❌ "Out of memory" ao processar

```bash
# Reduzir batch size em app/config/thresholds.jetson.yaml
# Procure por "batch_size:" e coloque 1

# Ou forçar FP32 (mais lento mas usa menos memória)
docker stop ar-diagnostic-mvp
docker run -d \
  --gpus all \
  --name ar-api-nano \
  -p 8000:8000 \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/models/cache:/app/models/cache \
  -e MODEL_PRECISION=fp32 \
  ar-diagnostic-mvp:nano \
  poetry run ar-api
```

---

## 📱 Conectar Frontend

```javascript
// src/config.js ou .env
export const API_URL = 'http://jetson:8000';
// ou via IP (descobrir com: ssh jetson "hostname -I")
export const API_URL = 'http://192.168.X.X:8000';
```

Depois:
```bash
npm start
```

Acesse o frontend e teste!

---

## 📸 Capturar pra Apresentação TCC

### 1. Screenshot do Swagger (sucesso)
```bash
# No navegador do seu PC
# Abra: http://jetson:8000/docs
# Print Screen → Salvar como "swagger_nano.png"
```

### 2. Fazer requisição e capturar resultado
```bash
# Na interface Swagger mesmo:
# 1. Vá em /api/v1/diagnose
# 2. Click "Try it out"
# 3. Click "Execute"
# 4. Screenshot da resposta
# → Salvar como "resultado_nano.png"
```

### 3. Performance em tempo real
```bash
# No terminal do Nano
sudo tegrastats

# Enquanto processa uma imagem:
# Print Screen → "performance_nano.png"
```

### 4. Logs para relatório
```bash
# Do seu PC
ssh jetson "docker logs ar-diagnostic-mvp" > nano_logs.txt

# Copiar pro seu PC
scp jetson:~/backend_tcc_mvp/logs/app.log ./nano_app_logs.log
```

---

## ✅ Checklist Antes de Apresentar

Marque cada item ✓

- [ ] Docker build completou sem erros
- [ ] Container sobe com `docker-compose up -d`
- [ ] Health check funciona: `curl jetson:8000/health`
- [ ] Swagger acessível: `http://jetson:8000/docs`
- [ ] Teste simples executa com sucesso (latência ~25s)
- [ ] Logs não mostram erros CUDA
- [ ] VRAM não fica 100% constantemente
- [ ] Screenshots salvos:
  - [ ] Swagger
  - [ ] Resultado
  - [ ] Performance
  - [ ] Logs
- [ ] Frontend conecta (se tem frontend)
- [ ] Plano B pronto (vídeo backup, slides, etc)
- [ ] Nano está ligada e testada

---

## 🎯 Workflow Dia da Apresentação

### Manhã (30 min antes)

```bash
# Do seu PC
ssh jetson

# Verificar sistema
jetson_release

# Verificar docker
docker ps

# Se não estiver rodando:
docker-compose up -d
docker logs -f ar-diagnostic-mvp
```

### Durante apresentação

1. **Abrir docs:** `http://jetson:8000/docs`
2. **Fazer requisição:** Click em `/api/v1/diagnose` → Try it out → Execute
3. **Enquanto processa (25s):**
   - Explique a arquitetura
   - Mostre o código
   - Compare com Desktop/Orin
4. **Ao terminar:**
   - Mostre resultado
   - Explique latência (normal pro Nano)
5. **Finalize:**
   - Mostre logs
   - Cite benchmarks
   - Conclusão sobre trade-offs

---

## ⏱️ Timeline Esperado

| Atividade | Tempo | Notas |
|-----------|-------|-------|
| Ler este guia | 10 min | You are here! |
| Build Docker | 40 min | ☕ Café (primeira vez) |
| Teste básico | 5 min | Health check |
| Teste full | 30 sec | Processamento |
| Capturar | 5 min | Screenshots |
| **Total** | **~60 min** | (mostly wait) |

---

## 📚 Referência Rápida — Copia e Cola

```bash
# ═══════════════════════════════════════════════════
# CONECTAR
ssh jetson

# ═══════════════════════════════════════════════════
# BUILD (primeira vez, 40 min)
cd ~/backend_tcc_mvp
docker build -f docker/Dockerfile.jetson-nano -t ar-diagnostic-mvp:nano .

# ═══════════════════════════════════════════════════
# RODAR
docker-compose up -d

# ═══════════════════════════════════════════════════
# VER LOGS
docker logs -f ar-diagnostic-mvp

# ═══════════════════════════════════════════════════
# TESTAR (do seu PC em outro terminal)
curl http://jetson:8000/health

# ═══════════════════════════════════════════════════
# SWAGGER (abrir no navegador)
http://jetson:8000/docs

# ═══════════════════════════════════════════════════
# MONITORAR
sudo tegrastats

# ═══════════════════════════════════════════════════
# PARAR
docker-compose down

# ═══════════════════════════════════════════════════
# LIMPAR TUDO (se precisar reconstruir)
docker system prune -f --all
docker build --no-cache -f docker/Dockerfile.jetson-nano -t ar-diagnostic-mvp:nano .
```

---

## 💡 Dicas Pro TCC

1. **Explique as limitações**
   - Nano = 4GB memória compartilhada
   - Por isso é lento (25-30s/diagnóstico)
   - Justifique usar Orin em produção

2. **Mostre comparação**
   - Desktop: 5.87s ✅ Rápido
   - Orin: 5.44s ⚡ Ótimo
   - Nano: 156s ⚠️ Educacional

3. **Tenha plano B**
   - Se Nano trava: mostre vídeo pre-gravado
   - Se wifi falha: screenshots já salvos
   - Se faltar tempo: mostre benchmark

4. **Capture evidência**
   - Screenshots funcionando
   - Logs com timestamp
   - Métricas de performance
   - Tudo salvo antes do dia!

5. **Praticar antes**
   - Execute tudo 1 dia antes
   - Teste de novo 1 hora antes
   - Tenha esperança! 🙏

---

## 📞 SOS — Última Tentativa

Se nada funcionar:

```bash
# Limpar TUDO
ssh jetson << 'EOF'
docker system prune -f --all
cd ~/backend_tcc_mvp
git pull origin main
docker build --no-cache -f docker/Dockerfile.jetson-nano -t ar-diagnostic-mvp:nano .
docker-compose up -d
docker logs -f ar-diagnostic-mvp
EOF
```

Se mesmo assim não funcionar:
- Reinicie o Nano: `ssh jetson "sudo reboot"`
- Aguarde 2 min
- Tente novamente

---

## ✨ Success!

Se você vê isto nos logs:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete
```

**PARABÉNS!** 🎉 Pode apresentar! 

Todos os endpoints funcionam:
- `GET /health` — Verificar status
- `POST /api/v1/diagnose` — Processar imagem
- `GET /docs` — Documentação interativa

---

**Última atualização:** 2026-04-11  
**Status:** ✅ Testado no Nano (v18.04 + Docker antigo)  
**Próximo passo:** `ssh jetson && docker-compose up -d`
