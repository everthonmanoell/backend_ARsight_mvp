# Testes Manuais — Como Executar

Todos os comandos devem ser rodados **a partir da raiz do projeto** (`backend_tcc_mvp/`).

---

## Configuração do ambiente de saída

Antes de rodar qualquer teste, defina o ambiente em `app/config/thresholds.yaml`:

```yaml
environment: legion   # 'legion' → outputs/legion/  |  'jetson' → outputs/jetson/
```

---

## `test_gpu.py` — Diagnóstico de GPU

Verifica se CUDA está disponível e exibe informações da GPU. Não carrega nenhum modelo.

### No Legion (desktop)
```bash
python3 tests/manual/test_gpu.py
```
Saída esperada: CUDA disponível, GPU NVIDIA detectada, memória ~8–16 GB.

### Na Jetson Nano
```bash
# Dentro do container
docker exec -it ar-diagnostic-mvp python3.8 tests/manual/test_gpu.py

# Ou diretamente na Jetson (sem Docker)
python3.8 tests/manual/test_gpu.py
```
Saída esperada: CUDA disponível, `CUDA version: 10.2`, GPU com ~4 GB.

---

## `test_illumination.py` — PDI isolado

Testa apenas a análise de iluminação (sem modelo LLM). Rápido, sem necessidade de GPU.

### No Legion
```bash
python3 tests/manual/test_illumination.py
```

### Na Jetson Nano
```bash
docker exec -it ar-diagnostic-mvp python3.8 tests/manual/test_illumination.py
```

---

## `test_pipeline.py` — Pipeline completo local

Carrega o modelo LLM diretamente na memória e processa um batch de 10 imagens.

> ⚠️ **Não rode enquanto o servidor Docker estiver em execução.**
> Duas instâncias do modelo simultaneamente causam OOM no Jetson Nano (4 GB).

### No Legion
```bash
# Certifique-se que environment: legion está no thresholds.yaml
python3 tests/manual/test_pipeline.py
```
Resultado salvo em `outputs/legion/pipeline_test_<timestamp>.json`.

### Na Jetson Nano
```bash
# 1. Para o servidor antes de rodar
docker stop ar-diagnostic-mvp

# 2. Altere o environment no YAML para 'jetson'
#    (faça isso no desktop antes de enviar via git/rsync, ou edite direto na Jetson)

# 3. Roda o teste dentro do container
docker run --rm \
  --runtime=nvidia \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/outputs:/app/outputs \
  backend_tcc_mvp:jetson \
  python3.8 tests/manual/test_pipeline.py
```
Resultado salvo em `outputs/jetson/pipeline_test_<timestamp>.json`.

---

## `test_pipeline_http.py` — Pipeline completo via HTTP ✅ recomendado para Jetson

Envia as 10 imagens para o servidor já em execução e exibe resultado idêntico ao
`test_pipeline.py`. **Não carrega modelo na memória do cliente** — zero risco de OOM.

### No Legion (servidor local)
```bash
# Sobe o servidor localmente primeiro
uvicorn app.api.main:app --host 0.0.0.0 --port 8000

# Em outro terminal, roda o teste (environment: legion no YAML)
python3 tests/manual/test_pipeline_http.py --host localhost
```
Resultado salvo em `outputs/legion/pipeline_http_<timestamp>.json`.

### Na Jetson Nano (servidor na Jetson, teste roda no desktop)
```bash
# 1. Verifique que o servidor está rodando na Jetson
curl http://192.168.1.5:8000/health

# 2. Altere o environment para 'jetson' no thresholds.yaml

# 3. Rode o teste do desktop apontando para o IP da Jetson
python3 tests/manual/test_pipeline_http.py --host 192.168.1.5
```
Resultado salvo em `outputs/jetson/pipeline_http_<timestamp>.json`.

#### Opções do script
| Argumento | Padrão | Descrição |
|---|---|---|
| `--host` | `192.168.1.5` | IP ou hostname do servidor |
| `--port` | `8000` | Porta do servidor |

---

## Comparativo entre os testes de pipeline

| | `test_pipeline.py` | `test_pipeline_http.py` |
|---|---|---|
| Onde roda o modelo | **local** (na máquina que executa) | **servidor** (Jetson ou desktop) |
| Risco de OOM no Nano | ⚠️ Alto (para o servidor antes) | ✅ Nenhum |
| Mede tempo PDI separado | ✅ Sim | ❌ Não (tempo total HTTP) |
| Requer servidor rodando | ❌ Não | ✅ Sim |
| Cenário recomendado | Testes locais no Legion | Validação em produção na Jetson |
