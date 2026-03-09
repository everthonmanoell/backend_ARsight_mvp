# Testes — AR Diagnostic MVP

Visão geral de todos os testes do projeto e como executá-los em cada ambiente.

## Estrutura

```
tests/
├── test_api.py          # Testes automatizados dos endpoints (pytest)
└── manual/
    ├── test_gpu.py              # Diagnóstico de GPU / CUDA
    ├── test_illumination.py     # PDI isolado (sem modelo LLM)
    ├── test_pipeline.py         # Pipeline completo local (carrega modelo na memória)
    └── test_pipeline_http.py    # Pipeline completo via HTTP (servidor já rodando)
```

---

## `test_api.py` — Testes automatizados (pytest)

Testa os endpoints `/diagnose/batch` e `/upload/batch` via `TestClient` (sem servidor externo).
Usa CPU e modelo Qwen para manter a execução rápida em CI.

```bash
# Rodar todos os testes
pytest tests/test_api.py -v

# Rodar um teste específico
pytest tests/test_api.py::test_health -v
```

> Compatível em qualquer ambiente (Legion ou Jetson), pois força `device='cpu'`.

---

## `tests/manual/` — Testes manuais

Ver [tests/manual/README.md](manual/README.md) para instruções detalhadas por ambiente.

---

## Saída dos resultados

Os JSONs gerados pelos testes manuais são salvos automaticamente em subpastas
de acordo com o `environment` definido em `app/config/thresholds.yaml`:

| `environment` no YAML | Pasta de saída     |
|------------------------|--------------------|
| `legion`               | `outputs/legion/`  |
| `jetson`               | `outputs/jetson/`  |

Para alternar entre os ambientes, edite `app/config/thresholds.yaml`:

```yaml
environment: legion   # ou: jetson
```
