# 🚀 INÍCIO RÁPIDO - AR Diagnostic MVP

Comece em 5 minutos!

## ⚡ Instalação Rápida

```bash
cd c:\Users\das9\TCC\backend_tcc_mvp

# Instalar com Poetry
poetry install

# Ou com pip
pip install -r requirements.txt
```

## 🎯 Executar API

```bash
# Com Poetry
poetry run ar-api

# Ou diretamente
python -m uvicorn app.api.main:app --reload --host 0.0.0.0 --port 8000
```

A API estará disponível em: http://localhost:8000

## 🧪 Testar Endpoints

### 1. Verificação de Saúde
```bash
curl http://localhost:8000/health
```

Saída esperada:
```json
{
  "status": "healthy",
  "model": "qwen",
  "device": "cuda",
  "quantization": "4-bit"
}
```

### 2. Extrair Apenas Métricas (rápido, sem LLM)
```powershell
curl.exe -X POST http://localhost:8000/metrics `
  -F "file=@data/illumination/adequate/normal_image1.jpg"
```

### 3. Diagnóstico de Imagem Única (com LLM)
```powershell
curl.exe -X POST http://localhost:8000/diagnose `
  -F "file=@data/illumination/underexposed/dark_image1.jpg"
```

### 4. Fazer Upload e Salvar Imagem
```powershell
curl.exe -X POST http://localhost:8000/upload `
  -F "file=@data/illumination/adequate/normal_image1.jpg"
```

### 5. Diagnóstico em Lote
```powershell
curl.exe -X POST http://localhost:8000/diagnose/batch `
  -F "files=@data/illumination/underexposed/dark_image1.jpg" `
  -F "files=@data/illumination/adequate/normal_image1.jpg" `
  -F "files=@data/illumination/overexposed/bright_image1.jpg"
```

### 6. Documentação Interativa (Swagger)
Abrir no navegador: http://localhost:8000/docs

**Veja [docs/ENDPOINT_EXAMPLES.md](docs/ENDPOINT_EXAMPLES.md) para exemplos detalhados**

## 🧪 Executar Testes

```bash
# Teste em lote com todas as imagens
python tests/test_illumination_batch.py

# Testes da API
poetry run pytest tests/test_api.py
```

## ⚙️ Configuração

Editar `app/config/thresholds.yaml`:

### Alterar Modelo
```yaml
models:
  default: qwen  # ou 'phi' para maior qualidade
```

### Alterar Dispositivo
```yaml
models:
  device: cuda  # ou 'cpu' ou 'auto'
```

### Ajustar Limiares
```yaml
rule_engine:
  illumination:
    underexposed_threshold: 0.35  # Menor = mais rigoroso
    overexposed_threshold: 0.75   # Maior = mais rigoroso
```

## 📊 Desempenho Esperado

### GPU (CUDA)
- **Qwen 0.5B**: ~1.2s por imagem, ~800MB VRAM
- **Phi-3 Mini**: ~1.8s por imagem, ~1.2GB VRAM

### CPU
- **Qwen 0.5B**: ~4.0s por imagem
- **Phi-3 Mini**: ~7.0s por imagem

## 🐛 Problemas Comuns

### Problema: `CUDA out of memory`
**Solução:** Mudar para modo CPU
```yaml
models:
  device: cpu
```

### Problema: `Import error`
**Solução:** Reinstalar dependências
```bash
poetry install --sync
```

### Problema: `Model not found`
**Solução:** Os modelos são baixados automaticamente na primeira execução. Aguarde ~2 minutos.

## 📝 Formato de Resposta da API

```json
{
  "status": "pass",  // ou "fail"
  "risk_level": "low",  // "low", "medium", "high"
  "explanation": "A cena apresenta iluminação ideal...",
  "metrics": {
    "illumination": 0.72,
    "illumination_label": "adequate",
    "mean_brightness": 0.65
  },
  "triggered_rules": [],  // Vazio para PASS
  "recommendations": []  // Presente apenas para FAIL
}
```

## 🔄 Próximos Passos

1. ✅ Testar API localmente
2. ✅ Executar teste em lote para validar precisão
3. 🚀 Implantar no Jetson (veja [docs/JETSON_DEPLOYMENT.md](docs/JETSON_DEPLOYMENT.md))
4. 📊 Comparar desempenho com versão completa
5. 🔄 Migrar melhorias de volta para `backend_tcc`

## 📚 Documentação

- README Completo: [README.md](README.md)
- Guia Jetson: [docs/JETSON_DEPLOYMENT.md](docs/JETSON_DEPLOYMENT.md)

## 🆘 Precisa de Ajuda?

1. Verificar logs: `tail -f logs/ar_diagnostic_mvp.log`
2. Verificar GPU: `python -c "import torch; print(torch.cuda.is_available())"`
3. Testar pipeline: `python tests/test_illumination_batch.py`
