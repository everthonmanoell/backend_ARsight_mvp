# MVP Diagnóstico AR: Framework de Avaliação de Qualidade de Iluminação

## Sumário Executivo

Este repositório implementa um produto viável mínimo (MVP) pronto para produção para diagnóstico de qualidade de iluminação em tempo real em cenas de realidade aumentada (AR) em plataformas embarcadas com recursos limitados. O sistema combina extração de características baseada em regras com modelos de linguagem pequenos (SLMs) para fornecer tanto avaliação estatística rápida quanto explicações semanticamente significativas das condições de iluminação em ambientes descentralizados de hardware.

O projeto aborda o desafio fundamental de implantar sistemas de diagnóstico específicos de domínio em plataformas de hardware heterogêneas, desde dispositivos de borda (Jetson Nano, 4GB VRAM) até sistemas GPU embarcados (Jetson AGX Orin) até estações de trabalho de desktop (GPUs NVIDIA RTX), mantendo contratos de API consistentes e garantias de desempenho mensuráveis. 

## Escopo do Projeto e Objetivos de Pesquisa

### Objetivo Principal

Desenvolver e validar um pipeline de diagnóstico de iluminação portátil e eficiente que:

1. Processe lotes de imagens capturadas de cenas de realidade aumentada
2. Classifique condições de iluminação em categorias de risco 
3. Gere métricas de características quantitativas e explicações em linguagem natural
4. Funcione dentro de restrições rigorosas de latência em hardware embarcado (objetivo: 3,5 segundos para lotes de 10 quadros)
5. Forneça resultados determinísticos e reproduzíveis em ambientes de implantação


### Ambientes Alvo

A implementação foi validada em três ambientes de execução distintos, cada um apresentando restrições e requisitos de otimização únicos:

1. **Jetson Nano (4GB VRAM, GPU Maxwell)**: Representa o limite inferior de complexidade de implantação, exigindo pilhas de software legado e compromissos fundamentais entre capacidade de modelo e consumo de recursos.
2. **Jetson AGX Orin (32GB VRAM, GPU Ampere)**: Representa um alvo moderno de implantação em borda com espaço computacional significativamente maior, mas ainda sujeito a restrições térmicas e de potência.
3. **Desktop Legion (x86_64, GPUs NVIDIA RTX)**: Serve como plataforma de referência de desempenho e desenvolvimento, sem limitações de sistema embarcado.

## Arquitetura do Sistema

### Pipeline de Alto Nível

O pipeline de diagnóstico funciona em duas fases distintas:

```
                        [Entrada: Lote de Imagens]
                               |
                    Fase 1: Extração de Características
                               |
              +------------------+------------------+
              |                  |                  |
         [Módulo PDI]    [Métricas de Brilho]  [Análise de Clipping]
              |                  |                  |
              +------------------+------------------+
                               |
                    Classificação via Motor de Regras
                               |
                    +----------+----------+
                    |                     |
              [Rótulos de Iluminação]    [Pontuações de Risco]
                    |                     |
                    +----------+----------+
                               |
                    Fase 2: Explicação com SLM
                               |
                  [Seleção SLM: Qwen/Phi/DialoGPT]
                               |
         [Engenharia de Prompt + Injeção de Contexto]
                               |
              [Geração de Explicação em Linguagem Natural]
                               |
                   [Relatório de Diagnóstico Final]
```

### Fase 1: Diagnóstico Físico de Iluminação (PDI)

O módulo PDI (implementado em `app/pdi/illumination.py`) realiza análise direta de estatísticas em nível de pixel para avaliar a qualidade de iluminação através de características engenheiradas:

**Métricas de Brilho:**
- Luminância média de pixels (escala normalizada 0-1)
- Desvio padrão de valores de pixel (indicador de uniformidade)
- Estatísticas baseadas em histograma para regiões claras e escuras

**Análise de Clipping:**
- Percentual de pixels abaixo do limiar do 5º percentil
- Percentual de pixels acima do limiar do 95º percentil
- Utilizados como indicadores de subexposição e superexposição respectivamente

**Análise de Canal de Cor:**
- Avaliação de iluminação por canal (RGB)
- Detecção de dominância de cor através de métricas de desequilíbrio de canal

**Classificação Determinística:**
O motor de regras em `app/core/rule_engine.py` aplica limites configurados em `app/config/thresholds.yaml` para emitir rótulos de iluminação discretos e pontuações de risco. Esta fase é inteiramente determinística e reproduzível em plataformas.

### Fase 2: Explicação Baseada em Modelo de Linguagem

Após classificação baseada em regras, o sistema aumenta o diagnóstico com explicação semântica através de um dos três modelos de linguagem pequenos (SLMs) suportados. A seleção do modelo representa um trade-off fundamental entre latência de inferência, qualidade de explicação e requisitos de hardware.

**Opções de Modelo:**

1. **DialoGPT-small (117M parâmetros):** Modelo conversacional otimizado para pegada de memória mínima. Selecionado como opção validada para Jetson Nano onde compatibilidade de pilha de software (JetPack 4.6, PyTorch 1.10, Python 3.6) e restrições de hardware (4GB VRAM compartilhada) tornam modelos maiores impráticos.

2. **Qwen2.5-0.5B (~500M parâmetros):** Modelo sintonizado para instrução que equilibra qualidade de explicação com latência prática. Recomendado para Jetson AGX Orin e Desktop Legion como opção de produção primária.

3. **Phi-3-mini (~3.8B parâmetros):** Opção de mais alta qualidade enfatizando coerência de explicação e raciocínio. Viável em Orin e Legion mas com custos de latência; não suportado em Nano.

A decisão de seleção do modelo é documentada em detalhe em [docs/MODEL_SELECTION.md](docs/MODEL_SELECTION.md).

### Orquestração do Pipeline de Processamento

O módulo `app/pipeline/illumination_pipeline.py` coordena operações das Fases 1 e 2, manipulando:

- Validação de lote e normalização de imagem
- Cálculo sequencial de PDI entre lote de quadro
- Agregação de métricas por quadro em resumos de nível de lote
- Seleção dinâmica de modelo e injeção de prompt
- Geração de resposta JSON de diagnóstico final

## Decisões de Otimização e Racional de Desempenho

### Restrições de Eficiência de Memória

O projeto reflete restrições fundamentais impostas por plataformas embarcadas. Jetson Nano, com 4GB de memória unificada compartilhada entre CPU e GPU, necessita otimização agressiva:

1. **Seleção de Modelo:** DialoGPT-small (~117MB em FP16) representa o maior modelo pré-treinado viável, deixando ~2GB para cálculo de PDI e overhead de framework.

2. **Formato de Precisão:** FP16 (meia precisão) é usado por padrão em todas as plataformas, reduzindo pressão de memória 50% comparado a FP32 com degradação de precisão negligenciável para este domínio de tarefa.

3. **Orientação por Lote:** O processamento é fundamentalmente orientado a lotes, permitindo amortização de custos de carregamento de modelo e agrupamento de quadros em operações de kernel GPU. O tamanho típico de lote é 10 quadros por solicitação de diagnóstico.

4. **Trade-offs de Quantização:** Quantização de 4 bits (via bitsandbytes) é investigada mas marcada como NÃO SUPORTADA em Jetson Nano devido a limitações de capacidade de cómputo da GPU Maxwell. O recurso está disponível e funcional em Orin (computação 8.7) e GPUs de desktop modernas.

### Estratégia de Otimização de Latência

Restrição de latência alvo: 3,5 segundos para lote de diagnóstico de 10 quadros. Isto impulsiona várias opções arquiteturais:

1. **Caminho Rápido de PDI:** O motor de regras funciona diretamente em estatísticas de pixel sem representações intermediárias, típicamente concluindo em < 100ms por quadro.

2. **Aquecimento de Modelo:** O sinalizador de configuração `warmup_on_startup: true` força carregamento de modelo durante inicialização de API, eliminando latência de início frio do caminho de solicitação voltado ao usuário.

3. **Decodificação Gulosa:** Para DialoGPT, seleção de token gulosa (vs. amostragem) é imposta para inferência determinística e mais rápida (embora com custo de qualidade leve).

4. **Controle de Comprimento de Prompt:** Modelos de prompt são deliberadamente restritos (`prompt_max_length) para reduzir tanto computação de janela de contexto quanto comprimento de saída de modelo.


## Ambientes de Execução Suportados

### Jetson Nano (4GB VRAM, JetPack 4.6)

**Pilha de Software Validada:**
- L4T R32.7.x (Núcleo validado)
- JetPack 4.6.x (Suporte oficial NVIDIA)
- Python 3.6.9 (Legado mas estável)
- PyTorch 1.10.0 (CUDA 10.2 compatível)
- CUDA 10.2 (GPU Maxwell, computação 5.3)
- Transformers 4.8.2 (Última versão compatível com PyTorch 1.10)
- Modelo Recomendado: DialoGPT-small (opção única suportada)

**Configuração:** Consulte [docs/JETSON_NANO_GUIDE.md](docs/JETSON_NANO_GUIDE.md)

**Desempenho de Lote:** Aproximadamente 3,4 segundos para lotes de 10 quadros com inferência DialoGPT-small. PDI contribui ~91ms por quadro; inferência de modelo ~250ms cumulativo.

### Jetson AGX Orin (32GB VRAM, JetPack 6.x)

**Pilha de Software Validada:**
- L4T R36.x (Moderno, suportado ativamente)
- JetPack 6.x (Padrão NVIDIA atual)
- Python 3.10 (Biblioteca padrão moderna)
- PyTorch 2.x (CUDA 12.x compatível)
- CUDA 12.x (GPU Ampere, computação 8.7)
- Transformers 4.4x+ (Suporta arquiteturas recentes)
- Modelo Recomendado: Qwen2.5-0.5B (melhor latência/qualidade)

**Configuração:** Consulte [docs/JETSON_ORIN_GUIDE.md](docs/JETSON_ORIN_GUIDE.md)

**Desempenho de Lote:** Aproximadamente 3,5 segundos para lotes de 10 quadros com Qwen2.5-0.5B. PDI contribui ~50ms por quadro; inferência de modelo ~250ms cumulativo. Phi-3-mini é viável mas resulta em latências de lote ~8-10 segundos.

### Desktop Legion (x86_64, GPU NVIDIA RTX)

**Pilha de Software Validada:**
- Ubuntu 22.04 LTS (Software de sistema)
- Python 3.10+ (Ambiente de desenvolvimento padrão)
- PyTorch 2.x (CUDA 12.x compatível)
- CUDA 12.x (Stack de driver de desktop)
- Transformers 4.4x+ (Não restringido por hardware)
- Modelo Recomendado: Qwen2.5-0.5B (padrão de produção)

**Configuração:** Consulte [docs/LEGION_GUIDE.md](docs/LEGION_GUIDE.md)

**Desempenho de Lote:** Plataforma de referência, típicamente 20-30% mais rápida que Orin para modelos equivalentes devido a suporte superior de conjunto de instruções x86 e pilhas de software maduras. Phi-3-mini é confortavelmente viável para cargas de trabalho de qualidade prioritária.


## Especificação de API

### Ponto de extremidade de Upload em Lote

**Endpoint:** `POST /upload/batch`

**Propósito:** Aceitar um lote de imagens para processamento de diagnóstico posterior.

**Solicitação:**
```
Dados multiformulários:
  arquivos: [imagem1.jpg, imagem2.jpg, ..., imagem10.jpg]
```

**Resposta (200 OK):**
```json
{
  "batch_id": "batch_20260331_150210_a1b2c3",
  "status": "uploaded",
  "files_saved": 3,
  "message": "Salvos 3/3 arquivos"
}
```

**Detalhes:**
- Suporta até 10 imagens por lote
- Imagens armazenadas em `data/uploads/{batch_id}/`
- ID de lote é determinístico baseado em timestamp, permitindo resiliência de retry
- Metadados persistidos em `metadata.json` dentro do diretório de lote

### Ponto de extremidade de Diagnóstico (Processamento em Lote)

**Endpoint:** `POST /diagnose/batch/{batch_id}`

**Propósito:** Realizar diagnóstico completo de iluminação em um lote carregado.

**Solicitação:**
```
JSON (parâmetros opcionais):
{
  "model_override": "qwen"  // Opcional, padrão conforme config
}
```

**Resposta (200 OK):**
```json
{
  "batch_id": "batch_20260331_150210_a1b2c3",
  "status": "completed",
  "summary": {
    "overall_risk": "ALTO|MÉDIO|BAIXO",
    "dominant_label": "subexposto|adequado|superexposto",
    "normal_count": 2,
    "problem_count": 1,
    "explanation": "Resumo em linguagem natural dos achados...",
    "recommendations": ["Ajustar configurações de exposição..."],
    "metrics_avg": {
      "mean_brightness": 0.65,
      "mean_luma": 165.75,
      "uniformity": 0.87,
      "pct_clipped_dark": 0.0,
      "pct_clipped_bright": 0.05
    },
    "processing_time_s": 3.82
  },
  "frames": [
    {
      "frame_index": 0,
      "filename": "frame_00.jpg",
      "risk_level": "NORMAL|PROBLEMA",
      "illumination_label": "subexposto|adequado|superexposto",
      "metrics": {
        "illumination_score": 0.92,
        "mean_brightness": 0.62,
        "uniformity": 0.89,
        "clipping_dark": 0.0,
        "clipping_bright": 0.0
      }
    }
  ]
}
```

**Detalhes:**
- Operação bloqueante (síncrona) retornando diagnóstico completo
- Processamento inclui Fase 1 de PDI e (opcionalmente) Fase 2 de SLM
- Métricas abrangentes por quadro agregadas em resumo de lote
- Geração de explicação requer um SLM configurado; pode ser contornada com `skip_llm: true`

### Ponto de extremidade de Verificação de Saúde

**Endpoint:** `GET /health`

**Resposta (200 OK):**
```json
{"status": "healthy"}
```

## Instalação e Configuração

### Início Rápido por Plataforma

#### Jetson Nano

```bash
cd ~/backend_tcc_mvp
cp pyproject-jetson-nano.toml pyproject.toml
poetry install --no-dev
export OPENBLAS_CORETYPE=ARMV8
poetry run ar-api
```

Para troubleshooting detalhado e configuração manual, consulte [docs/JETSON_NANO_GUIDE.md](docs/JETSON_NANO_GUIDE.md).

#### Jetson AGX Orin

```bash
cd ~/backend_tcc_mvp
cp pyproject-jetson-orin.toml pyproject.toml
poetry install
poetry run ar-api
```

Para troubleshooting detalhado e configuração manual, consulte [docs/JETSON_ORIN_GUIDE.md](docs/JETSON_ORIN_GUIDE.md).

#### Desktop Legion (Ubuntu/Linux)

```bash
cd ~/backend_tcc_mvp
cp pyproject-legion.toml pyproject.toml
poetry install
poetry run ar-api
```

Para troubleshooting detalhado e configuração manual, consulte [docs/LEGION_GUIDE.md](docs/LEGION_GUIDE.md).

### Pré-requisitos

Todas as plataformas requerem:
- Poetry (gerenciador de dependências Python)
- Python 3.6+ (versão varia por plataforma)
- PyTorch compatível com CUDA (verifique com `python3 -c "import torch; print(torch.cuda.is_available())"`)

### Configuração

Nível de log, seleção de modelo e limites de motor de regras são controlados através de `app/config/thresholds.yaml`:

```yaml
models:
  default: qwen              # Seleção de modelo: dialogpt-small | qwen | phi
  device: cuda               # Dispositivo: cuda | cpu | auto
  use_4bit: false            # Quantização de 4 bits (válido somente em Orin/Legion)
  greedy_decoding: true      # Inferência determinística (somente DialoGPT)
  prompt_max_length: 256     # Máx tokens de contexto para entrada de modelo
  warmup_on_startup: true    # Carregar modelo durante inicialização de API

dialogpt-small:
  name: /home/das9/models/DialoGPT-small
  max_tokens: 20
  summary_tokens: 32
  temperature: 0.3
  top_p: 0.85

qwen:
  name: Qwen/Qwen2.5-0.5B-Instruct
  max_tokens: 100
  summary_tokens: 150
  temperature: 0.3
  top_p: 0.85

phi:
  name: microsoft/Phi-3-mini-4k-instruct
  max_tokens: 120
  summary_tokens: 200
  temperature: 0.3
  top_p: 0.85

pipeline:
  enabled_metrics:
    - illumination

rule_engine:
  illumination:
    underexposed_threshold: 0.35
    overexposed_threshold: 0.75
```

## Índice de Documentação

Este repositório contém documentação técnica extensa organizada por tópico:

### Configuração e Implantação

- [docs/JETSON_NANO_GUIDE.md](docs/JETSON_NANO_GUIDE.md): Guia completo de configuração para Jetson Nano, incluindo pré-requisitos, troubleshooting e expectativas de desempenho.
- [docs/JETSON_ORIN_GUIDE.md](docs/JETSON_ORIN_GUIDE.md): Guia de configuração para Jetson AGX Orin com infraestrutura moderna e opções de otimização avançadas.
- [docs/LEGION_GUIDE.md](docs/LEGION_GUIDE.md): Guia de configuração de estação de trabalho de desktop para desenvolvimento e benchmarking de referência.

### Seleção de Modelo e Desempenho

- [docs/MODEL_SELECTION.md](docs/MODEL_SELECTION.md): Comparação abrangente de modelos de linguagem suportados (DialoGPT-small, Qwen2.5-0.5B, Phi-3-mini) com recomendações específicas da plataforma.

### Benchmark e Análise Comparativa

- [docs/BENCHMARK_COMPARISON_ANALYSIS.md](docs/BENCHMARK_COMPARISON_ANALYSIS.md): Análise de desempenho medido entre plataformas, modelos e tamanhos de lote. Contém dados de tempo brutos, estatísticas agregadas e razões de speedup.
- [BENCHMARK_SUMMARY.md](BENCHMARK_SUMMARY.md): Resumo executivo de resultados de benchmark com achados-chave.

### Recursos Adicionais

- [SETUP_INSTRUCTIONS.md](SETUP_INSTRUCTIONS.md): Passo a passo de configuração com padrões comuns de troubleshooting.
- [setup/TROUBLESHOOTING.md](setup/TROUBLESHOOTING.md): Guia abrangente de troubleshooting para problemas comuns de configuração e tempo de execução.


## Estrutura do Projeto

```
backend_tcc_mvp/
├── app/
│   ├── api/
│   │   ├── main.py                    # Ponto de entrada da aplicação FastAPI
│   │   └── routes.py                  # Definições de endpoint REST
│   ├── config/
│   │   ├── config.py                  # Carregador de configuração
│   │   └── thresholds.yaml            # Parâmetros do motor de regras
│   ├── core/
│   │   ├── rule_engine.py             # Regras de classificação
│   │   └── validators.py              # Validadores de métricas
│   ├── models/
│   │   ├── base_model.py              # Base abstrata para SLMs
│   │   ├── dialogpt_model.py           # Implementação DialoGPT-small
│   │   ├── qwen_model.py              # Implementação Qwen2.5-0.5B
│   │   └── phi_model.py               # Implementação Phi-3-mini
│   ├── pdi/
│   │   └── illumination.py            # Diagnóstico de Iluminação Física
│   ├── pipeline/
│   │   └── illumination_pipeline.py    # Orquestração de processamento em lote
│   └── utils/
│       └── templates.py               # Templates de prompts
├── data/
│   ├── illumination/                  # Imagens de amostra por categoria
│   │   ├── bright_overexposed/
│   │   ├── dark_underexposed/
│   │   ├── normal/
│   │   └── uploads/                   # Armazenamento de lote em tempo de execução
├── docs/
│   ├── JETSON_NANO_GUIDE.md           # Configuração e implantação de Nano
│   ├── JETSON_ORIN_GUIDE.md           # Configuração e implantação de Orin
│   ├── LEGION_GUIDE.md                # Configuração de estação de trabalho de desktop
│   ├── MODEL_SELECTION.md             # Comparação e seleção de modelo
│   └── BENCHMARK_COMPARISON_ANALYSIS.md  # Análise de desempenho
├── tests/
│   ├── test_api.py                    # Testes de integração da API
│   ├── test_api_quick.py              # Script de validação rápido
│   └── manual/                        # Utilitários de teste manual
├── setup/
│   ├── jetson-nano/                   # Scripts de configuração específicos de Nano
│   ├── jetson-orin/                   # Scripts de configuração específicos de Orin
│   └── legion-windows/                # Configuração de desktop (legado)
├── outputs/
│   ├── jetson-nano/                   # Saídas de benchmark de Nano
│   ├── jetson-orin/                   # Saídas de benchmark de Orin
│   ├── desktop-legion/                # Saídas de benchmark de desktop
│   └── benchmark_comparison/          # Resultados de análise comparativa
├── docker/
│   └── Dockerfile.jetson-nano         # Imagem de container para Nano
├── pyproject*.toml                    # Arquivos de configuração Poetry
│   ├── pyproject.toml                 # Genérico/desenvolvimento
│   ├── pyproject-jetson-nano.toml     # Dependências específicas de Nano
│   ├── pyproject-jetson-orin.toml     # Dependências específicas de Orin
│   └── pyproject-legion.toml          # Dependências específicas de desktop
├── README.md                          # Este arquivo
└── SETUP_INSTRUCTIONS.md              # Walkthrough detalhado de configuração
```

## Benchmark de Desempenho

### Executando Benchmarks

Para gerar medidas detalhadas de desempenho em seu hardware:

```bash
python benchmark_jetson_vs_legion.py
```

Este script:
1. Descobre todos os arquivos JSON de resultado em subdiretórios `outputs/`
2. Normaliza medidas de tempo e identificadores de modelo
3. Gera estatísticas comparativas por ambiente e modelo
4. Produz arquivos CSV para análise posterior
5. Gera um relatório Markdown com resumos estatísticos e visualizações

### Artefatos de Saída de Benchmark

Gerados em `outputs/benchmark_comparison/`:

- `runs_raw.csv`: Conjunto de dados completo de todos os lotes individuais e seus timings
- `summary_by_env_model_batch.csv`: Estatísticas agregadas por (ambiente, modelo, tamanho_lote)
- `speedup_legion_vs_jetson.csv`: Razões de speedup comparando desktop e desempenho embarcado
- `benchmark_report.md`: Análise legível por humano com achados-chave
- `plots/`: Visualizações (se matplotlib estiver instalado)

### Interpretando Resultados

Métricas-chave reportadas:

- **Latência Média:** Tempo médio de processamento de lote entre execuções
- **Desvio Padrão:** Desvio padrão de latência (indica consistência)
- **Taxa de Speedup:** Desempenho de desktop relativo ao embarcado (ex: 3.0 = 3x mais rápido)
- **Throughput:** Quadros por segundo para tamanho de lote e latência

## Técnicas de Otimização Aplicadas

### Otimização de Memória

1. **Precisão Mista (FP16):** Reduz pegada de memória 50% em todas as plataformas
2. **Seleção de Modelo:** Opções de modelo conservador para ambientes restritos
3. **Processamento em Lote:** Amortiza custos e overhead fixo
4. **Pipeline sem Estado:** Nenhum estado persistente entre solicitações

### Otimização de Inferência

1. **Aquecimento no Início:** Elimina latência de início frio de solicitações
2. **Decodificação Gulosa:** Geração mais rápida de token vs. amostragem
3. **Ajuste de Prompt:** Janelas de contexto mínimas reduzem computação
4. **Design Orientado a Características:** Caminho rápido baseado em regras antes da fase SLM opcional

### Considerações Específicas de Hardware

1. **Jetson Nano:** OPENBLAS_CORETYPE=ARMV8 para operações aceleradas por CPU
2. **Jetson Orin:** Stack CUDA 12.x moderno permite agendamento avançado de instrução
3. **Desktop Legion:** Otimização irrestrita, vantagens SIMD x86

## Limitações Conhecidas e Trade-offs

1. **Pilha de Software Jetson Nano:** Python 3.6 legado e PyTorch 1.10 limitam acesso a arquiteturas de modelo recentes e recursos de biblioteca. A opção validada DialoGPT-small representa a capacidade máxima dentro destas restrições.

2. **Orientação por Lote:** Esta implementação destina-se a processamento em lote com tamanhos típicos de 10 quadros. Streaming de quadro único em tempo real exigiria mudanças arquiteturais (decodificadores de streaming, enfileiramento de solicitação).

3. **Trade-off Determinístico vs. Qualidade:** Decodificação gulosa em DialoGPT garante reprodutibilidade com custo de qualidade leve comparado a geração baseada em amostragem.

4. **Quantização de Modelo:** Quantização de 4 bits não é suportada em GPU Maxwell (Jetson Nano). Isto limita otimização de memória na plataforma mais restrita.

## Trabalho Futuro e Integração

### Melhorias de Curto Prazo

1. Investigar seleção dinâmica de modelo baseada em tamanho de lote e orçamento de latência
2. Implementar enfileiramento de solicitação para submissões de lote concorrentes
3. Adicionar pontuação de confiança a classificações de iluminação

### Direções de Longo Prazo

1. Integração com sistema de diagnóstico AR completo cobrindo múltiplos atributos de cena
2. Fine-tuning de aprendizado de transferência em conjuntos de dados de iluminação específicos de domínio
3. Suporte de inferência de streaming para análise AR contínua
4. Processamento distribuído em múltiplos dispositivos embarcados

## Reprodutibilidade e Preservação de Artefato

Todas as medidas de benchmark, arquivos de configuração e resultados de validação são preservados na estrutura de diretório `outputs/` organizada por plataforma e timestamp. Isto permite:

1. Comparação reproduzível de mudanças de otimização
2. Validação contra metas de desempenho documentadas
3. Rastreamento histórico da evolução de capacidade da plataforma

Para reproduzir uma configuração de benchmark específica, consulte o diretório correspondente sob `outputs/`:

```bash
outputs/
├── jetson-nano/
│   ├── batch_10_qwen_*_result.json
│   ├── batch_10_dialogpt_*_result.json
│   └── summary.json
├── jetson-orin/
│   ├── batch_10_qwen_*_result.json
│   ├── batch_10_phi_*_result.json
│   └── summary.json
└── desktop-legion/
    ├── batch_10_qwen_*_result.json
    ├── batch_10_phi_*_result.json
    └── summary.json
```
l