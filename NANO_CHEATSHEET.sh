#!/bin/bash
# 📋 CHEAT SHEET - Jetson Nano (Copiar e Colar)

# ═══════════════════════════════════════════════════════════════════
# 🔌 CONECTAR
# ═══════════════════════════════════════════════════════════════════

ssh jetson
ssh jetson "ls ~/backend_tcc_mvp"

# ═══════════════════════════════════════════════════════════════════
# 🏗️  BUILD DOCKER (PRIMEIRA VEZ - 30-40min)
# ═══════════════════════════════════════════════════════════════════

ssh jetson << 'EOF'
cd ~/backend_tcc_mvp
docker build -f docker/Dockerfile.jetson-nano -t ar-diagnostic-mvp:nano .
EOF

# ═══════════════════════════════════════════════════════════════════
# 🚀 RODAR API - OPÇÃO 1 (Docker Compose - Fácil)
# ═══════════════════════════════════════════════════════════════════

ssh jetson << 'EOF'
cd ~/backend_tcc_mvp
docker compose -f docker-compose-nano.yml up
EOF

# ═══════════════════════════════════════════════════════════════════
# 🚀 RODAR API - OPÇÃO 2 (Docker Run - Simples)
# ═══════════════════════════════════════════════════════════════════

ssh jetson << 'EOF'
cd ~/backend_tcc_mvp
docker run -it --rm \
  --gpus all \
  --name ar-api-nano \
  -p 8000:8000 \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/models/cache:/app/models/cache \
  -e TRANSFORMERS_CACHE=/app/models/cache \
  -e AR_CONFIG_FILE=/app/app/config/thresholds.jetson.yaml \
  ar-diagnostic-mvp:nano \
  poetry run ar-api
EOF

# ═══════════════════════════════════════════════════════════════════
# ⏹️  PARAR API
# ═══════════════════════════════════════════════════════════════════

ssh jetson "docker compose -f ~/backend_tcc_mvp/docker-compose-nano.yml down"
# ou
ssh jetson "docker stop ar-api-nano"

# ═══════════════════════════════════════════════════════════════════
# 📊 TESTAR API
# ═══════════════════════════════════════════════════════════════════

# Health check
curl http://jetson:8000/health

# Ver Swagger (abrir no navegador)
# http://jetson:8000/docs

# ═══════════════════════════════════════════════════════════════════
# 📜 VER LOGS
# ═══════════════════════════════════════════════════════════════════

# Com Docker Compose
ssh jetson "docker compose -f ~/backend_tcc_mvp/docker-compose-nano.yml logs -f"

# Com Docker Run
ssh jetson "docker logs ar-api-nano -f"

# ═══════════════════════════════════════════════════════════════════
# ⚙️  MONITORAR PERFORMANCE (tempo real)
# ═══════════════════════════════════════════════════════════════════

ssh jetson "watch -n 1 'free -h && echo \"---\" && nvidia-smi'"
# ou
ssh jetson "sudo tegrastats"

# ═══════════════════════════════════════════════════════════════════
# 📋 VER STATUS DO CONTAINER
# ═══════════════════════════════════════════════════════════════════

ssh jetson "docker ps | grep ar-api"
ssh jetson "docker images | grep ar-diagnostic"

# ═══════════════════════════════════════════════════════════════════
# 🔍 DEBUG - Se algo falhar
# ═══════════════════════════════════════════════════════════════════

# Verificar CUDA
ssh jetson "nvidia-smi"

# Verificar JetPack
ssh jetson "jetson_release"

# Verificar Docker
ssh jetson "docker --version"

# Verificar projeto
ssh jetson "cd ~/backend_tcc_mvp && git status"

# ═══════════════════════════════════════════════════════════════════
# 🔧 LIMPEZA (se tiver problema de build/memória)
# ═══════════════════════════════════════════════════════════════════

# Limpar containers antigos
ssh jetson "docker system prune -f"

# Limpar imagens
ssh jetson "docker image prune -f"

# Limpar build cache
ssh jetson "docker builder prune --all -f"

# Reconstruir do zero
ssh jetson << 'EOF'
cd ~/backend_tcc_mvp
docker system prune -f --all
docker build -f docker/Dockerfile.jetson-nano --no-cache -t ar-diagnostic-mvp:nano .
EOF

# ═══════════════════════════════════════════════════════════════════
# 💾 COPIAR ARQUIVOS
# ═══════════════════════════════════════════════════════════════════

# Enviar arquivo pro Nano
scp meu_arquivo.txt jetson:~/

# Puxar arquivo do Nano
scp jetson:~/arquivo.txt .

# ═══════════════════════════════════════════════════════════════════
# 📈 FAZER BENCHMARK (para o TCC)
# ═══════════════════════════════════════════════════════════════════

# Rodar teste de performance e capturar resultado
ssh jetson << 'EOF'
cd ~/backend_tcc_mvp
docker exec ar-api-nano poetry run python tests/test_api_quick.py 2>&1 | tee resultado.txt
EOF

# Copiar resultado
scp jetson:~/backend_tcc_mvp/resultado.txt ./nano_resultado.txt

# ═══════════════════════════════════════════════════════════════════
# 🎬 USAR COM FRONTEND
# ═══════════════════════════════════════════════════════════════════

# Descobrir IP do Nano
NANO_IP=$(ssh jetson "hostname -I | awk '{print \$1}'")
echo "IP do Nano: $NANO_IP"

# Usar no frontend
# API_URL="http://jetson:8000"
# ou
# API_URL="http://$NANO_IP:8000"

# ═══════════════════════════════════════════════════════════════════
# ⏱️  USAR SCRIPT INTERATIVO
# ═══════════════════════════════════════════════════════════════════

# Dar permissão
chmod +x setup-nano.sh

# Menu completo
./setup-nano.sh

# Ou direto
./setup-nano.sh --build      # Build
./setup-nano.sh --run        # Rodar
./setup-nano.sh --stop       # Parar
./setup-nano.sh --logs       # Logs
./setup-nano.sh --test       # Teste rápido

# ═══════════════════════════════════════════════════════════════════
# 📱 DICAS PRO TCC
# ═══════════════════════════════════════════════════════════════════

# 1. Screenshot do Swagger da API funcionando
#    - Abra http://jetson:8000/docs
#    - Tire screenshot

# 2. Capturar latência real enquanto processa
#    - Deixe tegrastats rodando
#    - Tire screenshot com métrica

# 3. Comparar com Desktop/Orin
#    - Rode benchmark: poetry run python benchmark_jetson_vs_legion.py
#    - Mostre gráfico: outputs/benchmark_comparison/plots/

# 4. Ter backup do vídeo
#    - Se Nano travar na apresentação
#    - Mostre vídeo pré-gravado funcionando

# ═══════════════════════════════════════════════════════════════════
