# Poetry Setup para Jetson Nano

## Passo 1: Instalar Poetry

Na sua máquina (não no Nano), execute:

```bash
ssh jetson "bash ~/tcc/backend_tcc_mvp/install_poetry_nano.sh"
```

Isso vai:
- ✅ Instalar pip3, setuptools e wheel
- ✅ Instalar Poetry 1.1.15 (compatível com Python 3.6)
- ✅ Configurar Poetry para criar venvs locais

## Passo 2: Adicionar Poetry ao PATH (Permanente)

Entre no Nano via SSH e execute:

```bash
ssh jetson
echo 'export PATH=$HOME/.local/bin:$PATH' >> ~/.bashrc
source ~/.bashrc
```

Verifique:
```bash
poetry --version
```

Deve mostrar: `Poetry version 1.1.15`

## Passo 3: Instalar Dependências com Poetry

No Nano, navegue até o projeto e execute setup:

```bash
ssh jetson
cd ~/tcc/backend_tcc_mvp
git pull origin main  # Pega script novo
bash setup_poetry_nano.sh
```

Esse script vai:
- ✅ Usar Poetry para instalar dependências de pyproject-jetson-nano.toml
- ✅ Instalar torch 1.10.0 da Jetson AI Lab (com CUDA)
- ✅ Fazer fallback para requirements-jetson-nano.txt se necessário
- ✅ Testar CUDA com tensor

## Passo 4: Testar GPU

Depois que o setup terminar:

```bash
cd ~/tcc/backend_tcc_mvp
poetry run python -c "import torch; print(f'CUDA available: {torch.cuda.is_available()}')"
```

**Esperado:** `CUDA available: True`

Se receber False, verifique logs em `docker logs ar-diagnostic-mvp`

## Passo 5: Rodar API com Poetry

```bash
cd ~/tcc/backend_tcc_mvp
poetry run python -m uvicorn app.api.main:app --host 0.0.0.0 --port 8000
```

## Troubleshooting

### Poetry command not found
Se `poetry: command not found`:
```bash
export PATH=$HOME/.local/bin:$PATH
poetry --version
```

### CUDA não disponível após instalação
```bash
# Check torch
poetry run python -c "import torch; print(torch.__version__)"

# Check if CUDA installed
poetry run python -c "import torch; print(torch.cuda.get_device_name(0))"

# Reinstall torch
poetry run pip install --force-reinstall --no-cache-dir \
    torch==1.10.0 \
    --index-url https://pypi.jetson-ai-lab.io/jp46/cu102
```

### Erro no setup_poetry_nano.sh
Se o script falhar:
1. Verifique que Poetry está instalado: `poetry --version`
2. Verifique que está em ~/tcc/backend_tcc_mvp: `pwd`
3. Execute com debug: `bash -x setup_poetry_nano.sh`
4. Veja logs: `cat /tmp/poetry-setup.log`

## Scripts Principais

- **install_poetry_nano.sh** — Instala Poetry no Nano (execute na máquina local via SSH)
- **setup_poetry_nano.sh** — Configura projeto com Poetry e instala deps
- **pyproject-jetson-nano.toml** — Configuração Poetry para Nano
- **requirements-jetson-nano.txt** — Fallback pip para Nano

## Timing Esperado

| Etapa | Tempo |
|-------|-------|
| Instalar Poetry | 2-3 min |
| setup_poetry_nano.sh | 5-10 min (primeira vez) |
| Testar CUDA | <10 seg |
| Rodar API | <30 seg |

## Próximas Etapas após GPU Working

1. Testar batch inference
2. Verificar se tempo baixou de 29.5s para ~3s
3. Atualizar benchmarks
