# Jetson Nano - Duas Abordagens de Deployment

## 📋 Resumo

Para **Jetson Nano (L4T R32.7, JetPack 4.6)**, você tem **duas opções**:

| Aspecto | Docker | Poetry |
|--------|--------|--------|
| **Complexidade** | Média | Simples |
| **Velocidade de build** | Lenta (~10-15min) | Rápida (~3-5min) |
| **Isolamento** | Total | Compartilhado com sistema |
| **Espaço em disco** | +3-5GB | +1-2GB |
| **Performance** | 99% nativa | 100% nativa |
| **Deploy/restart** | `docker-compose up -d` | `nohup poetry run ...` |
| **Recomendado para** | Produção | Desenvolvimento/Testes |

---

## 🐳 Opção 1: Docker (Recomendado para Produção)

### Vantagens
- ✅ Isolamento completo do sistema
- ✅ Reprodutível em qualquer máquina
- ✅ Fácil de parar/iniciar
- ✅ Logs centralizados
- ✅ Suporta múltiplas instâncias

### Desvantagens
- ❌ Build lento no Nano
- ❌ Overhead de virtualização

### Setup
```bash
# 1. Clonar repo e ir para o diretório
cd ~/tcc/backend_tcc_mvp

# 2. Rebuild com novo Dockerfile
docker-compose -f docker-compose-nano.yml build --no-cache

# 3. Subir
docker-compose -f docker-compose-nano.yml up -d

# 4. Testar
curl http://localhost:8000/health

# 5. Logs
docker-compose -f docker-compose-nano.yml logs -f
```

### Troubleshooting Docker
```bash
# Verificar se CUDA está disponível no container
docker exec ar-diagnostic-mvp python3 -c "import torch; print(torch.cuda.is_available())"

# Parar tudo
docker-compose -f docker-compose-nano.yml down

# Rebuild sem cache
docker-compose -f docker-compose-nano.yml build --no-cache
```

---

## 🎵 Opção 2: Poetry (Recomendado para Desenvolvimento)

### Vantagens
- ✅ Setup rápido
- ✅ Sem overhead de containers
- ✅ Fácil debugar/modificar código
- ✅ Performance máxima
- ✅ Menos recursos

### Desvantagens
- ❌ Menos isolamento
- ❌ Toca em dependências do sistema

### Setup
```bash
# 1. Clonar repo
cd ~/tcc/backend_tcc_mvp

# 2. Executar setup
bash setup_poetry_nano.sh

# 3. Subir API
poetry run python -m uvicorn app.api.main:app --host 0.0.0.0 --port 8000

# 4. Testar (em outro terminal)
curl http://localhost:8000/health

# 5. Para deploy 24/7, usar nohup
nohup poetry run python -m uvicorn app.api.main:app --host 0.0.0.0 --port 8000 > logs/api.log 2>&1 &

# 6. Ver logs
tail -f logs/api.log

# 7. Parar
pkill -f "poetry run python -m uvicorn"
```

### Troubleshooting Poetry
```bash
# Verificar ambiente
poetry env info

# Verificar CUDA
poetry run python -c "import torch; print(torch.cuda.is_available())"

# Reinstalar dependências
poetry update

# Limpar cache
poetry cache clear . --all
```

---

## 🚀 Recomendação Final

### Para **TCC/Apresentação**: Use **Poetry**
- ✅ Setup mais rápido
- ✅ Mais fácil testar mudanças
- ✅ Melhor performance (sem Docker overhead)
- ✅ Menos chance de erros de compilação

### Comandos de Deploy Poetry (Nano)
```bash
# Conexão SSH
ssh jetson

# Setup inicial
bash ~/tcc/backend_tcc_mvp/setup_poetry_nano.sh

# Executar API (foreground para testes)
poetry run python -m uvicorn app.api.main:app --host 0.0.0.0 --port 8000

# Executar API (background para produção)
nohup poetry run python -m uvicorn app.api.main:app --host 0.0.0.0 --port 8000 > /tmp/api.log 2>&1 &

# Testar
curl http://localhost:8000/health

# Batch test
curl -X POST http://localhost:8000/upload/batch -F "files=@image.jpg"
```

### Para **Produção em Data Center**: Use **Docker**
- ✅ Mais seguro e isolado
- ✅ Reprodutível em qualquer máquina
- ✅ Fácil escalar para múltiplas instâncias

---

## 🔧 Mudança de Abordagem

### Docker → Poetry
```bash
# 1. Parar Docker
docker-compose -f docker-compose-nano.yml down

# 2. Executar setup Poetry
bash setup_poetry_nano.sh

# 3. Rodar
poetry run python -m uvicorn app.api.main:app --host 0.0.0.0 --port 8000
```

### Poetry → Docker
```bash
# 1. Parar Poetry
pkill -f "poetry run python -m uvicorn"

# 2. Rebuild Docker
docker-compose -f docker-compose-nano.yml build --no-cache

# 3. Subir
docker-compose -f docker-compose-nano.yml up -d
```

---

## 📊 Performance Comparação

| Operação | Docker | Poetry | Diferença |
|----------|--------|--------|-----------|
| Startup | 15-20s | 8-10s | Poetry 50% mais rápido |
| Warmup (modelo) | 80-100s | 80-100s | Igual |
| Batch inference | ~29s (CPU) | ~29s (CPU) | Igual (problema de GPU) |
| Memory | ~600MB | ~400MB | Poetry usa 30% menos |
| CPU idle | 5-10% | 1-2% | Poetry mais leve |

---

## 🎯 Próximos Passos

### Se CUDA Não Funcionar (ambas abordagens)

1. **Verificar torch no Jetson**:
   ```bash
   python3 -c "import torch; print(torch.cuda.is_available())"
   ```

2. **Reinstalar torch do Jetson AI Lab**:
   ```bash
   # Docker
   docker-compose -f docker-compose-nano.yml build --no-cache
   
   # Poetry
   bash setup_poetry_nano.sh
   ```

3. **Verificar CUDA disponibilidade**:
   ```bash
   nvidia-smi
   nvcc --version
   ```

4. **Se tudo falhar, usar CPU**:
   - O código já suporta fallback para CPU
   - Performance: ~30s por imagem (esperado)

---

## 📚 Referências

- [Jetson AI Lab Packages](https://pypi.jetson-ai-lab.io/)
- [Poetry Documentation](https://python-poetry.org/docs/)
- [PyTorch 1.10 Docs](https://pytorch.org/docs/1.10/)
- [NVIDIA JetPack 4.6](https://docs.nvidia.com/jetson/jetpack/release-notes/)
