# 🎯 Passo-a-Passo Nano para TCC

## Objetivo
Rodar a API completa na Jetson Nano para demonstração de um sistema em hardware limitado.

---

## 📋 PASSO 1: Preparação (5 min)

### 1.1 Do seu PC, conecte ao Nano
```bash
ssh jetson
```

**Esperado:**
```
jetson@jetson-nano:~$
```

### 1.2 Verifique acesso ao projeto
```bash
ls ~/backend_tcc_mvp
```

**Esperado:** Vê arquivos como `app/`, `docker/`, `docker-compose-nano.yml`

### 1.3 Volte pro seu PC
```bash
exit
```

✅ **Status:** Conectividade OK

---

## 🏗️ PASSO 2: Build Docker (40 min)

⏱️ **TEMPO: 30-40 minutos** ☕️ Café!

### 2.1 Inicie o build (do seu PC)
```bash
ssh jetson << 'EOF'
cd ~/backend_tcc_mvp
docker build -f docker/Dockerfile.jetson-nano -t ar-diagnostic-mvp:nano .
EOF
```

**Esperado:** Vê output:
```
Sending build context to Docker daemon
Step 1/10 : FROM nvcr.io/nvidia/l4t-pytorch:r32.7.1-pth1.10-py3
...
Step 10/10 : ENV NVIDIA_DRIVER_CAPABILITIES=compute,utility
Successfully tagged ar-diagnostic-mvp:nano
```

### 2.2 Monitore progresso (opcional, em outro terminal)
```bash
ssh jetson "docker ps -a --all"
# ou
ssh jetson "watch -n 5 'docker images | grep ar'"
```

✅ **Status:** Build em andamento (volte quando terminar)

---

## ✨ PASSO 3: Verificar Build (2 min)

### 3.1 Confirme que a imagem foi criada
```bash
ssh jetson "docker images | grep ar-diagnostic"
```

**Esperado:**
```
ar-diagnostic-mvp   nano   SHA   40 minutes ago   3.2GB
```

✅ **Status:** Docker pronto!

---

## 🚀 PASSO 4: Rodar a API (1 min)

### Opção A: Com Docker Compose (Simples)

```bash
ssh jetson << 'EOF'
cd ~/backend_tcc_mvp
docker compose -f docker-compose-nano.yml up
EOF
```

### Opção B: Com Docker Run (Alternativa)

```bash
ssh jetson << 'EOF'
cd ~/backend_tcc_mvp
docker run -it --rm \
  --gpus all \
  --name ar-api-nano \
  -p 8000:8000 \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/models/cache:/app/models/cache \
  -e TRANSFORMERS_CACHE=/app/models/cache \
  ar-diagnostic-mvp:nano \
  poetry run ar-api
EOF
```

**Esperado após alguns segundos:**
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete
```

✅ **Status:** API rodando!

---

## 🧪 PASSO 5: Testar a API (2 min)

### 5.1 Health check (do seu PC em novo terminal)
```bash
curl http://jetson:8000/health
```

**Esperado:**
```json
{"status":"ok"}
```

### 5.2 Abra Swagger (navegador)
```
http://jetson:8000/docs
```

**Esperado:** Interface Swagger interativa

### 5.3 Teste uma requisição via Swagger

Na interface:
1. Clique no endpoint `/api/v1/diagnose`
2. Clique "Try it out"
3. Modifique o JSON (se quiser)
4. Clique "Execute"

**Esperado:** Resposta com resultado da análise (vai demorar 20-30s)

✅ **Status:** API funcionando!

---

## 📊 PASSO 6: Monitorar Performance (contínuo)

**Nova seção em terminal separado:**

```bash
ssh jetson "watch -n 1 'free -h | grep Mem && echo --- && nvidia-smi --query-gpu=memory.used,memory.total --format=csv,noheader,nounits'"
```

**Esperado:**
```
Mem:         3.8Gi        2.1Gi        ...
---
2100 / 4000
```

✅ **Indicador:** Memória não deve passar de ~90%

---

## ✅ PASSO 7: Capturar para Apresentação TCC

### 7.1 Screenshot Swagger (sucesso)
```
Abrir: http://jetson:8000/docs
Print Screen → Salvar como "nano_swagger.png"
```

### 7.2 Screenshot de resultado
```
Na interface Swagger:
- Execute uma requisição
- Screenshot da resposta
→ Salvar como "nano_resposta.json"
```

### 7.3 Screenshot do Console
```
Deixar tegrastats rodando:
ssh jetson "sudo tegrastats"

Enquanto processa imagem:
Print Screen → "nano_performance.png"
```

### 7.4 Logs para relatório
```bash
ssh jetson "docker logs ar-api-nano > ~/nano_logs.txt"
scp jetson:~/nano_logs.txt ./
```

---

## ⏹️ PASSO 8: Parar Quando Terminar

### Opção A: Com Docker Compose
```bash
ssh jetson "docker compose -f ~/backend_tcc_mvp/docker-compose-nano.yml down"
```

### Opção B: Com Ctrl+C
Na tela onde `docker run` está rodando:
```
Ctrl+C
```

**Esperado:**
```
Shutting down...
INFO:     Shutdown complete
```

✅ **Status:** API parada

---

## ⏱️ Timeline Resumido

```
Total: ~50 minutos (mostly espera)

├─ PASSO 1 (Prep):      5 min    ✓ Rápido
├─ PASSO 2 (Build):     40 min   ☕ Café!
├─ PASSO 3 (Verify):    2 min    ✓ Rápido
├─ PASSO 4 (Run):       1 min    ✓ Rápido
├─ PASSO 5 (Test):      2 min    ✓ Rápido
├─ PASSO 6 (Monitor):   ~ min    ▶️ Contínuo
├─ PASSO 7 (Capture):   5 min    ✓ Documentação
└─ PASSO 8 (Stop):      1 min    ✓ Limpeza
```

---

## 🆘 Se Algo Der Errado

### ❌ "Build falhou com erro de memória"
```bash
ssh jetson << 'EOF'
# Aumentar swap
sudo fallocate -l 4G /var/swapfile
sudo chmod 600 /var/swapfile
sudo mkswap /var/swapfile
sudo swapon /var/swapfile

# Tentar build novamente
cd ~/backend_tcc_mvp
docker build --no-cache -f docker/Dockerfile.jetson-nano -t ar-diagnostic-mvp:nano .
EOF
```

### ❌ "API não responde"
```bash
# Ver logs
ssh jetson "docker logs ar-api-nano"

# Se erro CUDA, reiniciar Nano
ssh jetson "sudo reboot"

# Aguarde 2 min, reconecte:
ssh jetson
# Recomece PASSO 4
```

### ❌ "Connection refused ao acessar"
```bash
# Verificar se container está rodando
ssh jetson "docker ps | grep ar-api"

# Se não está, subir novamente (PASSO 4)
```

---

## 💡 Dicas Importantes

1. **Faça tudo ANTES da apresentação**
   - Build Docker é longo
   - Teste tudo com calma
   - Tenha backup de screenshots

2. **Deixe Nano ligada durante a demonstration**
   - Não desligue
   - Evite reiniciar

3. **Tenha plano B**
   - Se falhar: mostrar vídeo pré-gravado
   - Benchmark já pronto pra mostrar

4. **Explique as limitações**
   - Nano = 4GB memória compartilhada
   - Por isso é lento (20-30s)
   - Justifique uso de Orin em produção

5. **Compare os resultados**
   - Desktop: 5.87s ✓ Rápido
   - Orin: 5.44s ✓ Ótimo
   - Nano: 156s ⚠️ Lento mas funciona!

---

## 📁 Arquivos Gerados/Usados

| Arquivo | Uso |
|---------|-----|
| `NANO_TUTORIAL.md` | Documentação completa |
| `NANO_CHEATSHEET.sh` | Comandos rápidos |
| `setup-nano.sh` | Script interativo |
| `docker-compose-nano.yml` | Configuração Docker |
| `docker/Dockerfile.jetson-nano` | Receita Docker |

---

## ✅ Checklist Final

Antes de apresentar:

- [ ] Build completou sem erros
- [ ] Container sobe e e responde
- [ ] Health check funciona
- [ ] Swagger accessible em browser
- [ ] Teste simples executa com sucesso
- [ ] Latência está ~20-30s (normal pra Nano)
- [ ] VRAM não fica 100%
- [ ] Screenshots salvos
- [ ] Logs salvos
- [ ] Plano B pronto (vídeo backup)

---

## 🎓 O que Mostrar no TCC

1. **Estado do sistema:**
   - JetPack version
   - GPU temperature/usage
   - Memory usage during processing

2. **API funcionando:**
   - Request → Response com sucesso
   - Latência real (20-30s)
   - Accuracy resultado

3. **Comparação:**
   - Gráficos de Nano vs Orin vs Desktop
   - Tabela de performance
   - Explicação de trade-offs

4. **Conclusão:**
   - Nano = viável mas lento
   - Orin = recommended para produção
   - Desktop = development/testing

---

**Última atualização:** 2026-04-10  
**Teste e valide ANTES de apresentar! 🎯**
