# 🧪 Como Testar o Fix de Upload na Jetson Nano

## Passo 1: Inicie a API

Em um terminal, na pasta do backend:

```bash
poetry run ar-api
```

Aguarde até ver:
```
✅ API ready to accept requests!
INFO:     Uvicorn running on http://0.0.0.0:8000
```

## Passo 2: Execute o teste em outro terminal

Na mesma pasta:

```bash
python test_batch_flow.py
```

Ou especifique uma URL diferente se necessário:

```bash
python test_batch_flow.py http://192.168.15.X:8000
```

## O que o teste faz

1. **Cria 10 imagens de teste** com variações de brilho
2. **Faz upload** via `/upload/batch` 
3. **Verifica** se todos os 10 frames foram aceitos (antes do fix: 7/10)
4. **Inicia diagnóstico** via `/diagnose/batch/:id`
5. **Mostra resultados** com métricas de cada frame

## Resultado esperado ANTES do fix

```
Validation error for frame_0.jpg: Invalid image file: argument out of range
Validation error for frame_1.jpg: Invalid image file: argument out of range
Batch batch_... created with 7/10 files  ❌
```

## Resultado esperado DEPOIS do fix

```
✓ UPLOAD SUCCESS: Todos os 10 frames aceitos!
✓ DIAGNÓSTICO CONCLUÍDO
  Frames processados: 10  ✅
  Sucesso: 10/10
```

## Logs esperados na API

**ANTES (rejeitava frames):**
```
2026-04-12 20:13:00,817 - app.api.routes - ERROR - Validation error for frame_0.jpg: Invalid image file: argument out of range
2026-04-12 20:13:00,859 - app.api.routes - ERROR - Validation error for frame_1.jpg: Invalid image file: argument out of range
```

**DEPOIS (tolera metadados ruins):**
```
2026-04-12 20:13:00,817 - app.api.routes - WARNING - EXIF transpose failed for frame_0.jpg: [error details]
2026-04-12 20:13:00,859 - app.api.routes - INFO - Processing 10 frames for batch batch_...
```

## Análise rápida dos logs

Se você ver `Processing X frames for batch` com X=10 (ao invés de X=7), o fix funcionou! ✅
