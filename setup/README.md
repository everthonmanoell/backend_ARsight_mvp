# Setup - AR Diagnostic MVP

Escolha seu ambiente:

## 🐧 Jetson Orin (Linux / JetPack 6.x)

Para configurar o ambiente em **Jetson Orin** (AGX Orin ou Orin NX):

```bash
cd ~/backend_tcc_mvp
bash setup/jetson-orin/setup.sh
```

**Documentação:** [setup/jetson-orin/README.md](jetson-orin/README.md)

Requirements:
- JetPack 6.0+
- CUDA 12.6
- Python 3.10+
- Poetry

---

## 🪟 Desktop Legion (Windows)

Para configurar o ambiente em **PC Legion com Windows** (RTX 3080/4090):

**Opção 1: PowerShell (Recomendado)**
```powershell
cd C:\Users\<seu_usuario>\TCC\backend_tcc_mvp\setup\legion-windows
.\setup.ps1
```

**Opção 2: Command Prompt (cmd.exe)**
```cmd
cd C:\Users\<seu_usuario>\TCC\backend_tcc_mvp\setup\legion-windows
setup.bat
```

**Documentação:** [setup/legion-windows/README.md](legion-windows/README.md)

Requirements:
- Windows 10/11
- NVIDIA GPU (RTX 20 series ou mais novo)
- CUDA 12.1+ drivers
- Python 3.10+
- Poetry

---

## ⚠️ Troubleshooting

Se encontrar problemas:

1. **CUDA não encontrado:** Ver [setup/legion-windows/README.md](legion-windows/README.md#cuda-não-encontrado)
2. **Poetry lock fails:** Ver [Troubleshooting](TROUBLESHOOTING.md)
3. **Import errors:** Verifique a versão de Python com `python --version`

---

## 🚀 Próximos Passos

Após o setup ser concluído:

### Rodar a API
```bash
# Jetson
poetry run ar-api

# Windows
poetry run ar-api
```

### Executar Pipeline de Teste
```bash
# Ambos
poetry run python tests/manual/test_pipeline.py
```

### Rodar Testes Unitários
```bash
# Ambos
poetry run pytest tests/
```

---

## 📁 Estrutura

```
setup/
├── README.md                          (este arquivo)
├── TROUBLESHOOTING.md                 (soluções comuns)
├── jetson-orin/
│   ├── setup.sh                       (script de setup)
│   └── README.md                      (instruções detalhadas)
└── legion-windows/
    ├── setup.ps1                      (script de setup)
    ├── README.md                      (instruções detalhadas)
    └── CUDA_SETUP.md                  (guia CUDA para Windows)
```

---

## 📖 Documentação Adicional

- [SETUP_INSTRUCTIONS.md](../SETUP_INSTRUCTIONS.md) - Guia completo de instalação
- [README.md](../README.md) - Documentação geral do projeto
- [JETSON_SETUP.md](../JETSON_SETUP.md) - Detalhes específicos de Jetson
