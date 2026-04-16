# Estrutura do Projeto - Backend TCC MVP

## 📁 Organização de Diretórios

```
backend_tcc_mvp/
│
├── app/                         # 🎯 CÓDIGO PRINCIPAL (Arquitetura Modular)
│   ├── __init__.py             # Inicialização do pacote
│   │
│   ├── api/                    # API REST
│   │   ├── __init__.py
│   │   ├── main.py            # FastAPI app (initialização)
│   │   └── routes.py          # Endpoints da API
│   │
│   ├── core/                   # Lógica de Negócio
│   │   ├── __init__.py
│   │   ├── rule_engine.py     # Motor de regras determinísticas
│   │   └── validators.py      # Validação de saídas dos modelos
│   │
│   ├── models/                 # Implementações de Modelos LLM
│   │   ├── __init__.py
│   │   ├── base_model.py      # Classe abstrata base para modelos
│   │   ├── dialogpt_model.py  # Implementação DialoGPT
│   │   ├── phi_model.py       # Implementação Phi
│   │   └── qwen_model.py      # Implementação Qwen
│   │
│   ├── pdi/                    # PDI - Processamento Digital de Imagens
│   │   ├── __init__.py
│   │   └── illumination.py    # Análise de iluminação em imagens
│   │
│   ├── pipeline/               # Pipeline de Processamento
│   │   ├── __init__.py
│   │   └── illumination_pipeline.py  # Pipeline end-to-end de análise
│   │
│   ├── config/                 # Configuração
│   │   ├── __init__.py
│   │   ├── config.py          # Configurações centralizadas
│   │   ├── thresholds.yaml    # Limiares de iluminação (produção)
│   │   └── thresholds.jetson.yaml  # Limiares otimizados (Jetson)
│   │
│   └── utils/                  # Utilitários
│       ├── __init__.py
│       └── templates.py        # Templates de respostas
│
├── benchmarks/                 # 📊 BENCHMARKS E TESTES DE PERFORMANCE
│   ├── README.md              # Documentação de benchmarks
│   ├── START_HERE.md          # Guia rápido para executar benchmarks
│   ├── BENCHMARK_QUICK_REFERENCE.sh  # Script quick reference
│   ├── BENCHMARKING_GUIDE.md  # Guia completo de benchmarking
│   │
│   ├── scripts/               # Scripts de benchmark
│   │   ├── analyze_perf.py           # Análise de performance
│   │   ├── benchmark_jetson_vs_legion.py  # Comparação Jetson vs Legion
│   │   ├── compare_perf.py           # Comparação de resultados
│   │   ├── generate_comparison_report.py  # Geração de relatórios
│   │   ├── check_baseline.py         # Validação de baseline
│   │   ├── check_config.py           # Verificação de configurações
│   │   ├── check_final.py            # Validação final
│   │   ├── check_latest.py           # Verificação de latest
│   │   └── README.md                 # Documentação dos scripts
│   │
│   ├── reports/               # Relatórios gerados
│   │   ├── README.md
│   │   ├── BENCHMARK_SUMMARY.md      # Resumo de benchmarks
│   │   ├── BENCHMARK_UPDATE.md       # Atualizações recentes
│   │   └── CHANGELOG_BENCHMARKS.md   # Histórico de mudanças
│   │
│   ├── outputs/               # Resultados de benchmarks
│   │   ├── README.md
│   │   ├── comparison/        # Comparações entre modelos
│   │   └── legacy/            # Resultados históricos
│   │
│   ├── data/                  # Dados de teste
│   │   └── README.md
│   │
│   └── INDEX.txt              # Índice de arquivos
│
├── data/                       # 📂 DADOS DO PROJETO
│   ├── illumination/          # Imagens de teste classificadas
│   │   ├── bright_overexposed/    # Imagens super exposed
│   │   ├── dark_underexposed/     # Imagens sub exposed
│   │   └── normal/                # Imagens normais
│   │
│   └── uploads/               # Uploads de usuários (produção)
│       ├── 20260315_143220/
│       ├── batch_20260331_175013_603452/
│       └── ...
│
├── outputs/                    # 📈 RESULTADOS DE EXECUÇÕES
│   ├── desktop-legion/        # Resultados (Desktop Legion)
│   ├── jetson-nano/           # Resultados (Jetson Nano)
│   └── jetson-orin/           # Resultados (Jetson Orin)
│
├── tests/                      # ✅ TESTES
│   ├── __init__.py
│   ├── test_api.py            # Testes da API REST
│   ├── test_api_quick.py      # Testes rápidos da API
│   ├── test_batch_flow.py     # Testes do fluxo em lote
│   ├── test_cuda_quick.py     # Testes CUDA rápidos
│   │
│   └── manual/                # Testes manuais
│
├── docker/                     # 🐳 CONTAINERIZAÇÃO
│   └── Dockerfile.jetson-nano # Dockerfile para Jetson Nano
│
├── docs/                       # 📚 DOCUMENTAÇÃO
│   ├── STRUCTURE.md           # Este arquivo - Arquitetura do projeto
│   ├── API_GUIDE.md           # Guia da API REST
│   ├── MODEL_SELECTION.md     # Guia de seleção de modelos
│   ├── JETSON_NANO_GUIDE.md   # Deploy em Jetson Nano
│   ├── JETSON_ORIN_GUIDE.md   # Deploy em Jetson Orin
│   ├── LEGION_GUIDE.md        # Deploy em desktop (Legion)
│   ├── BATCH_PERFORMANCE_ANALYSIS.md  # Análise de performance batch
│   └── CHANGELOG.md           # Histórico de mudanças
│
├── logs/                       # 📋 LOGS (em tempo de execução)
│
├── .gitignore
├── README.md                   # 📖 Documentação principal
├── requirements.txt            # Dependências Python (padrão)
├── requirements-jetson.txt     # Dependências (Jetson)
├── pyproject.toml             # Project metadata (padrão)
├── pyproject-jetson-nano.toml # Project metadata (Jetson Nano)
├── pyproject-jetson-orin.toml # Project metadata (Jetson Orin)
├── pyproject-legion.toml      # Project metadata (Legion)
├── docker-compose.yml         # Docker Compose para containerização
├── setup_legion.ps1           # Setup para Windows (Legion)
├── setup_jetson_orin.sh       # Setup para Linux (Jetson Orin)
├── setup_poetry_nano.sh       # Setup para Linux (Jetson Nano)
│
└── notebooks/                 # 🔬 NOTEBOOKS JUPYTER (análise)
```

## 🏗️ Arquitetura Modular

### 1. API (Interfaces HTTP)

**`api/main.py`**
- Inicializa FastAPI
- Configuração de middlewares
- Setup de CORS

**`api/routes.py`**
- Endpoints da API REST
- Integração com pipeline de processamento
- Tratamento de requisições e respostas

### 2. Core (Lógica de Negócio)

**`core/rule_engine.py`**
- Classe `RuleEngine`: Implementa regras determinísticas para diagnóstico
- Métodos principais:
  - `evaluate(metrics)`: Avalia métricas de iluminação
  - `get_evidence_metrics(metrics)`: Formata métricas para explicação
  - `build_recommendations(triggered_rules)`: Gera recomendações

**`core/validators.py`**
- Classe `OutputValidator`: Valida saídas dos modelos LLM
- Métodos:
  - `is_valid_explanation(text, metrics)`: Verifica qualidade da explicação
  - `sanitize_explanation(text)`: Remove artefatos

### 3. Models (Implementações de Modelos LLM)

**`models/base_model.py`**
- Classe abstrata `ARDiagnosticModel`
- Define interface comum para todos os modelos
- Implementa padrão híbrido: regras + LLM + validação
- Métodos abstratos:
  - `_load_model()`: Carregamento do modelo
  - `_call_model(prompt)`: Inferência do modelo
  - `_build_prompt(...)`: Construção do prompt

**`models/dialogpt_model.py`**
- Classe `DialogPTModel`: Implementação Microsoft DialoGPT
- Características: Conversacional, leve

**`models/phi_model.py`**
- Classe `PhiModel`: Implementação Microsoft Phi
- Características: Eficiente, otimizado para edge computing

**`models/qwen_model.py`**
- Classe `QwenModel`: Implementação Qwen
- Características: Multilíngue, performance equilibrada

### 4. PDI (Processamento Digital de Imagens)

**`pdi/illumination.py`**
- Classe `IlluminationAnalyzer`: Análise de iluminação em imagens
- Métodos:
  - `analyze_brightness()`: Analisa nível de brilho
  - `analyze_contrast()`: Analisa contraste
  - `analyze_color_balance()`: Analisa balanço de cores
  - `detect_overexposure()`: Detecta regiões super expostas
  - `detect_underexposure()`: Detecta regiões sub expostas
  - `get_illumination_histogram()`: Retorna histograma de iluminação

### 5. Pipeline (Fluxo de Processamento)

**`pipeline/illumination_pipeline.py`**
- Classe `IlluminationPipeline`: Orquestra todo o fluxo
- Fluxo completo:
  1. Recebe imagem
  2. Processa com PDI (extrai métricas)
  3. Aplica regras do RuleEngine
  4. Gera explicação com modelo LLM
  5. Valida saída com OutputValidator
  6. Retorna resultado estruturado

### 6. Config (Configuração)

**`config/config.py`**
- Classe `Config`: Centraliza configurações do projeto
- Carrega thresholds de YAML
- Configurações por ambiente (jetson/legion/produção)

**`config/thresholds.yaml`** / **`thresholds.jetson.yaml`**
- Limiares para detecção de problemas de iluminação
- Separação por hardware (diferentes limiares para Jetson vs Desktop)

### 7. Utils (Utilitários)

**`utils/templates.py`**
- Classe `ExplanationTemplates`
- Templates em linguagem natural para respostas
- Fallback quando LLM falha na validação
- Garante respostas de qualidade mesmo com falhas

## 🔄 Fluxo de Execução

```
1. Cliente faz requisição HTTP à API
   ↓
2. Rota recebe imagem/métricas
   ↓
3. IlluminationPipeline inicializa
   ↓
4. IlluminationAnalyzer processa imagem
   │  └─ Extrai: brightness, contrast, color_balance, etc.
   ↓
5. RuleEngine avalia métricas (determinístico)
   │  └─ Retorna: status, risk_level, triggered_rules
   ↓
6. Modelo LLM gera explicação textual
   │  └─ (DialoGPT, Phi ou Qwen, configurável)
   ↓
7. OutputValidator verifica qualidade
   │  ├─ ✅ Válido → Retorna explicação LLM
   │  └─ ❌ Inválido → Retorna template fallback
   ↓
8. API retorna JSON estruturado
```

## 🎯 Benefícios da Arquitetura Modular

### Separação de Responsabilidades
- **API**: Apenas interface HTTP
- **Core**: Lógica de negócio isolada (regras)
- **Models**: Implementações de LLM independentes
- **PDI**: Análise de imagens isolada
- **Pipeline**: Orquestração sem lógica de negócio

### Extensibilidade Facilitada
- **Adicionar novo modelo**: Herdar de `ARDiagnosticModel` e implementar 3 métodos
- **Adicionar nova regra**: Editar apenas `RuleEngine.evaluate()`
- **Adicionar novo endpoint**: Criar rota em `api/routes.py` com pipeline existente
- **Aceitar novos formatos**: Estender `IlluminationAnalyzer`

### Testabilidade
- Cada módulo pode ser testado isoladamente
- Mocks facilitados pela separação clara de responsabilidades
- Testes em `tests/` para cada componente

### Manutenibilidade
- Código organizado e fácil de navegar
- Imports claros e explícitos
- Reduz acoplamento entre componentes
- Fácil deprecar componentes antigos

### Multi-Hardware
- Diferentes `thresholds.*yaml` para cada plataforma
- Diferentes `pyproject-*.toml` para dependências otimizadas
- Setup scripts específicos para cada ambiente

## 📝 Comparação: Setup Antigo vs Novo

### Antes (Monolítico)
```
├── ar_diagnostic_dialogpt.py (300+ linhas)
├── ar_diagnostic_phi3.py (300+ linhas)
├── ar_diagnostic_qwen.py (300+ linhas)
│
Cada arquivo = código duplicado
├── ❌ Regras embutidas (duplicadas)
├── ❌ Validação embutida (duplicada)
├── ❌ Templates embutidos (duplicados)
└── ❌ Carregamento embutido (duplicado)
```
- ❌ Difícil manter sincronizados
- ❌ Mudanças devem ser feitas em 3 arquivos
- ❌ Boas práticas espalhadas
- ❌ Alto risco de inconsistências

### Depois (Modular)
```
app/
├── core/rule_engine.py (1 fonte de verdade)
├── core/validators.py
├── models/base_model.py (classe abstrata compartilhada)
├── models/dialogpt_model.py (100 linhas apenas)
├── models/phi_model.py (100 linhas apenas)
├── models/qwen_model.py (100 linhas apenas)
└── pipeline/illumination_pipeline.py
```
- ✅ Cada módulo testável independentemente
- ✅ Mudanças em 1 local (DRY principle)
- ✅ Fácil adicionar novos modelos
- ✅ Fácil adicionar novas regras
- ✅ Código mais legível e organizado
- ✅ Deploy otimizado por hardware (thresholds específicos)

## 🔧 Como Usar a Estrutura

### Executar Servidor API
```bash
python -m uvicorn app.api.main:app --reload
```

### Executar Testes
```bash
pytest tests/
```

### Adicionar Novo Modelo LLM
```python
# app/models/novo_modelo.py
from app.models.base_model import ARDiagnosticModel

class NovoModelo(ARDiagnosticModel):
    def _load_model(self):
        # Carrega o modelo
        pass
    
    def _call_model(self, prompt):
        # Executa inferência
        return response
    
    def _build_prompt(self, metrics, rules_triggered):
        # Constrói prompt customizado
        return prompt
```

### Adicionar Nova Regra
```python
# app/core/rule_engine.py - no método evaluate()
if metrics['new_metric'] > NEW_THRESHOLD:
    triggered_rules.append("nova_regra_diagnostico")
    risk_level = max(risk_level, "medium")
```

### Adicionar Novo Endpoint
```python
# app/api/routes.py
@router.post("/novo-endpoint")
async def novo_endpoint(dados: NovosDados):
    pipeline = IlluminationPipeline()
    resultado = await pipeline.process(dados)
    return resultado
```

### Deploy em Jetson Nano
```bash
./setup_poetry_nano.sh
# Usa pyproject-jetson-nano.toml e thresholds.jetson.yaml
```

## 📂 Organização por Ambiente

| Ambiente | Config | Setup | Thresholds |
|----------|--------|-------|-----------|
| Desktop (Legion) | `pyproject-legion.toml` | `setup_legion.ps1` | `thresholds.yaml` |
| Jetson Nano | `pyproject-jetson-nano.toml` | `setup_poetry_nano.sh` | `thresholds.jetson.yaml` |
| Jetson Orin | `pyproject-jetson-orin.toml` | `setup_jetson_orin.sh` | `thresholds.yaml` |
| Docker | - | `docker-compose.yml` | `thresholds.jetson.yaml` |

## 📊 Benchmarking

Os scripts em `benchmarks/scripts/` permitem:
- Comparar performance entre modelos
- Medir latência em diferentes hardwares
- Gerar relatórios de performance
- Validar baselines de performance

## 📚 Documentação Adicional

- [README.md](../README.md): Documentação principal do projeto
- [API_GUIDE.md](./API_GUIDE.md): Endpoints e uso da API
- [MODEL_SELECTION.md](./MODEL_SELECTION.md): Comparação de modelos
- [JETSON_NANO_GUIDE.md](./JETSON_NANO_GUIDE.md): Deploy Jetson Nano
- [JETSON_ORIN_GUIDE.md](./JETSON_ORIN_GUIDE.md): Deploy Jetson Orin
- [LEGION_GUIDE.md](./LEGION_GUIDE.md): Deploy em desktop
- [BATCH_PERFORMANCE_ANALYSIS.md](./BATCH_PERFORMANCE_ANALYSIS.md): Análise de performance
- [benchmarks/BENCHMARKING_GUIDE.md](../benchmarks/BENCHMARKING_GUIDE.md): Guia de benchmarks
