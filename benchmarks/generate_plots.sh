#!/bin/bash
# Quick script to generate all benchmark plots

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PLOTS_SCRIPTS_DIR="$SCRIPT_DIR/plots_scripts"

echo "╔════════════════════════════════════════════════════════════╗"
echo "║      Gerando Gráficos de Benchmark                         ║"
echo "╚════════════════════════════════════════════════════════════╝"

cd "$PLOTS_SCRIPTS_DIR"

echo ""
echo "📂 Diretório: $PLOTS_SCRIPTS_DIR"
echo ""

# Verificar se poetry está disponível
if command -v poetry &> /dev/null; then
    echo "✅ Poetry encontrado, usando poetry run..."
    poetry run python generate_all.py
else
    echo "⚠️  Poetry não encontrado, tentando python direto..."
    python generate_all.py
fi

echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║  ✅ Gráficos gerados com sucesso!                         ║"
echo "╚════════════════════════════════════════════════════════════╝"

PLOTS_OUTPUT="$SCRIPT_DIR/plots_output"
echo ""
echo "📂 Arquivos salvos em: $PLOTS_OUTPUT"
echo ""
echo "📊 Arquivos gerados:"
ls -lh "$PLOTS_OUTPUT"/*.png 2>/dev/null || echo "   (nenhum PNG encontrado ainda)"
echo ""

if [ -f "$PLOTS_OUTPUT/index.html" ]; then
    echo "📄 Relatório HTML:"
    echo "   $PLOTS_OUTPUT/index.html"
    echo ""
    echo "💡 Para abrir no navegador:"
    echo "   open $PLOTS_OUTPUT/index.html"
fi

echo ""
echo "Done! ✨"
