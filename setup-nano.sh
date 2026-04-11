#!/bin/bash
# 🐳 setup-nano.sh - Configurar e rodar API na Jetson Nano automaticamente

set -e

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuráveis
NANO_HOST="${NANO_HOST:-jetson}"
DOCKER_TAG="ar-diagnostic-mvp:nano"
COMPOSE_FILE="docker-compose-nano.yml"
API_PORT="8000"

# Função helper
log() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

success() {
    echo -e "${GREEN}[✓]${NC} $1"
}

error() {
    echo -e "${RED}[✗]${NC} $1"
    exit 1
}

warning() {
    echo -e "${YELLOW}[!]${NC} $1"
}

print_header() {
    echo ""
    echo "╔════════════════════════════════════════╗"
    echo "║  🚀 Jetson Nano API Setup              ║"
    echo "║  $1"
    echo "╚════════════════════════════════════════╝"
    echo ""
}

# ─────────────────────────────────────────────────────
# Main Menu
# ─────────────────────────────────────────────────────

main_menu() {
    print_header "Menu Principal"
    echo "Opções:"
    echo "  1) Build da imagem Docker (SSH)"
    echo "  2) Rodar API (Docker Compose)"
    echo "  3) Rodar API (Docker Run manual)"
    echo "  4) Parar API"
    echo "  5) Ver logs"
    echo "  6) Teste rápido da API"
    echo "  7) Monitorar performance"
    echo "  8) Full setup + Run (tudo de uma vez)"
    echo "  9) Sair"
    echo ""
    read -p "Escolha (1-9): " choice
}

# ─────────────────────────────────────────────────────
# Build Docker
# ─────────────────────────────────────────────────────

build_docker() {
    print_header "Build Docker - Jetson Nano"
    
    log "Conectando ao Nano ($NANO_HOST)..."
    
    ssh ${NANO_HOST} << 'ENDSSH'
    set -e
    cd ~/backend_tcc_mvp
    
    echo "[1/3] Preparando build..."
    docker --version > /dev/null 2>&1 || {
        echo "❌ Docker não instalado!"
        exit 1
    }
    
    echo "[2/3] Construindo imagem Docker..."
    echo "⚠️  Isto pode levar 30-40 minutos... ☕"
    docker build \
        -f docker/Dockerfile.jetson-nano \
        -t ar-diagnostic-mvp:nano \
        .
    
    echo "[3/3] Verificando build..."
    docker images | grep ar-diagnostic-mvp | grep nano
ENDSSH
    
    success "Docker build completo!"
}

# ─────────────────────────────────────────────────────
# Run avec Docker Compose
# ─────────────────────────────────────────────────────

run_compose() {
    print_header "Rodar API com Docker Compose"
    
    log "Enviando comando para Nano..."
    
    ssh ${NANO_HOST} << 'ENDSSH'
    set -e
    cd ~/backend_tcc_mvp
    
    echo "Parando containers anteriores..."
    docker compose -f docker-compose-nano.yml down 2>/dev/null || true
    
    echo "Subindo API..."
    docker compose -f docker-compose-nano.yml up
ENDSSH
}

# ─────────────────────────────────────────────────────
# Run com Docker Run
# ─────────────────────────────────────────────────────

run_docker_run() {
    print_header "Rodar API com Docker Run"
    
    log "Enviando comando para Nano..."
    
    NANO_IP=$(ssh ${NANO_HOST} "hostname -I | awk '{print \$1}'")
    
    ssh ${NANO_HOST} << ENDSSH
    set -e
    cd ~/backend_tcc_mvp
    
    # Parar se existir anterior
    docker stop ar-api-nano 2>/dev/null || true
    docker rm ar-api-nano 2>/dev/null || true
    
    # Rodar
    docker run -it --rm \
        --gpus all \
        --name ar-api-nano \
        -p ${API_PORT}:8000 \
        -v \$(pwd)/data:/app/data \
        -v \$(pwd)/models/cache:/app/models/cache \
        -v \$(pwd)/logs:/app/logs \
        -e TRANSFORMERS_CACHE=/app/models/cache \
        -e AR_CONFIG_FILE=/app/app/config/thresholds.jetson.yaml \
        ar-diagnostic-mvp:nano \
        poetry run ar-api
ENDSSH
}

# ─────────────────────────────────────────────────────
# Parar API
# ─────────────────────────────────────────────────────

stop_api() {
    print_header "Parar API"
    
    log "Parando containers..."
    
    ssh ${NANO_HOST} << 'ENDSSH'
    docker compose -f ~/backend_tcc_mvp/docker-compose-nano.yml down 2>/dev/null || true
    docker stop ar-api-nano 2>/dev/null || true
    docker rm ar-api-nano 2>/dev/null || true
ENDSSH
    
    success "API parada!"
}

# ─────────────────────────────────────────────────────
# Ver Logs
# ─────────────────────────────────────────────────────

show_logs() {
    print_header "Logs da API"
    
    log "Conectando ao Nano para logs..."
    
    ssh ${NANO_HOST} << 'ENDSSH'
    docker compose -f ~/backend_tcc_mvp/docker-compose-nano.yml logs -f --tail=50 2>/dev/null || \
    docker logs ar-api-nano -f 2>/dev/null || \
    echo "Nenhum container rodando"
ENDSSH
}

# ─────────────────────────────────────────────────────
# Teste Rápido
# ─────────────────────────────────────────────────────

quick_test() {
    print_header "Teste Rápido da API"
    
    # Descobrir IP
    NANO_IP=$(ssh ${NANO_HOST} "hostname -I | awk '{print \$1}'")
    
    log "Testando API em ${NANO_IP}:${API_PORT}..."
    
    # Health check
    log "Fazendo health check..."
    if curl -s http://${NANO_IP}:${API_PORT}/health | grep -q "ok"; then
        success "✓ API respondendo!"
    else
        error "✗ API não respondendo. Verifique os logs."
    fi
    
    # Swagger
    log "Documentação Swagger disponível em:"
    echo "  http://${NANO_IP}:${API_PORT}/docs"
    echo "  ou via SSH: http://jetson:${API_PORT}/docs"
    
    success "Teste completo!"
}

# ─────────────────────────────────────────────────────
# Monitorar Performance
# ─────────────────────────────────────────────────────

monitor_perf() {
    print_header "Monitorar Performance (Tempo Real)"
    
    warning "Você será conectado ao Nano em modo interativo"
    warning "Tecle 'q' para sair ou Ctrl+C"
    echo ""
    
    ssh ${NANO_HOST} << 'ENDSSH'
    watch -n 1 '
    echo "=== MEMÓRIA ==="
    free -h | grep -E "Mem:|Swap:"
    
    echo ""
    echo "=== GPU ==="
    nvidia-smi --query-gpu=name,memory.used,memory.total,utilization.gpu \
        --format=csv,noheader,nounits
    
    echo ""
    echo "=== CONTAINERS ==="
    docker ps --format "table {{.Names}}\t{{.Status}}"
    '
ENDSSH
}

# ─────────────────────────────────────────────────────
# Full Setup + Run
# ─────────────────────────────────────────────────────

full_setup() {
    print_header "Setup Completo + Run"
    
    warning "Isto vai:"
    warning "  1. Build a imagem (30-40 min)"
    warning "  2. Rodar a API"
    warning ""
    read -p "Continuar? (s/n) " -n 1 -r
    echo
    
    if [[ ! $REPLY =~ ^[Ss]$ ]]; then
        log "Cancelado"
        return
    fi
    
    build_docker
    echo ""
    log "Aguarde 5 segundos antes de rodar..."
    sleep 5
    run_compose
}

# ─────────────────────────────────────────────────────
# Main Loop
# ─────────────────────────────────────────────────────

main() {
    while true; do
        main_menu
        
        case $choice in
            1) build_docker ;;
            2) run_compose ;;
            3) run_docker_run ;;
            4) stop_api ;;
            5) show_logs ;;
            6) quick_test ;;
            7) monitor_perf ;;
            8) full_setup ;;
            9)
                echo ""
                log "Até logo! 👋"
                exit 0
                ;;
            *)
                error "Opção inválida ($choice)"
                ;;
        esac
        
        echo ""
        read -p "Pressione Enter para continuar..."
    done
}

# Verificar argumentos
if [[ $# -gt 0 ]]; then
    case $1 in
        --host)
            NANO_HOST=$2
            ;;
        --build)
            build_docker
            exit 0
            ;;
        --run)
            run_compose
            exit 0
            ;;
        --stop)
            stop_api
            exit 0
            ;;
        --logs)
            show_logs
            exit 0
            ;;
        --test)
            quick_test
            exit 0
            ;;
        --help)
            echo "Uso: $0 [opções]"
            echo "  --host HOSTNAME  Usar host diferente (padrão: jetson)"
            echo "  --build          Build Docker"
            echo "  --run            Rodar API"
            echo "  --stop           Parar API"
            echo "  --logs           Ver logs"
            echo "  --test           Teste rápido"
            echo "  --help           Esta mensagem"
            exit 0
            ;;
        *)
            error "Opção desconhecida: $1"
            ;;
    esac
fi

# Menu interativo
main
