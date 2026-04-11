# 📚 Índice Nano - Qual arquivo usar?

## Para Começar AGORA

### 🎯 Você quer...

#### "Quero saber por onde começo?"
→ Leia: **`NANO_PASSO_A_PASSO.md`**
- Passo-a-passo visual em ordem
- Tempo estimado pra cada etapa
- O que esperar em cada fase

#### "Quero um guia completo com explicações"
→ Leia: **`NANO_TUTORIAL.md`**
- Setup básico
- Troubleshooting detalhado
- Dicas pro TCC
- Componentes explicados

#### "Só me dá os comandos pra copiar/colar"
→ Use: **`NANO_CHEATSHEET.sh`**
- Copia e cola direto
- Menu de opções
- Debug rápido

#### "Quer automatizar tudo com menus?"
→ Execute: **`./setup-nano.sh`**
```bash
chmod +x setup-nano.sh
./setup-nano.sh
```

---

## 📖 Descrição dos Arquivos

### 1. `NANO_PASSO_A_PASSO.md` ⭐ COMECE AQUI
**Best for:** Apresentação visual passo-a-passo

```
Estrutura:
├─ Objetivo claro
├─ 8 passos em ordem
├─ Tempo estimado por passo
├─ Screenshots esperados
├─ Timeline resumida
├─ Se algo der errado (soluções)
├─ Dicas pro TCC
└─ Checklist final
```

**Quando usar:** Primeira vez ou preparar apresentação

---

### 2. `NANO_TUTORIAL.md` 📚 REFERÊNCIA COMPLETA
**Best for:** Entender tudo em profundidade

```
Estrutura:
├─ Setup SSH
├─ Build Docker (detalhes)
├─ 3 formas de rodar API
├─ Como testar
├─ Conectar frontend
├─ Troubleshooting (9 problemas)
├─ Script de automação
├─ Benchmark esperado
├─ Checklist final
└─ Referências rápidas (tabelas)
```

**Quando usar:** Precisa entender o "porquê" de cada passo

---

### 3. `NANO_CHEATSHEET.sh` ⚡ COPIA E COLA
**Best for:** Executar rápido sem ler

```
Estrutura:
├─ Conectar SSH
├─ Build Docker (1 comando)
├─ Rodar API (2 opções)
├─ Parar API
├─ Testar
├─ Logs
├─ Monitorar
├─ Debug
├─ Limpeza
├─ Copiar arquivos
├─ Benchmark
├─ Frontend
└─ Script interativo
```

**Quando usar:** "Só me dá o comando!"

---

### 4. `setup-nano.sh` 🎯 MENU INTERATIVO
**Best for:** Não quer digitar comandos

```
Menu:
1) Build Docker
2) Rodar (compose)
3) Rodar (manual)
4) Parar
5) Logs
6) Teste
7) Monitor
8) Full setup
9) Sair
```

**Quando usar:** Quer ponto-e-clique

---

## 🚀 Quick Start

### Opção 1: Automático (Recomendado)
```bash
chmod +x setup-nano.sh
./setup-nano.sh
# → Menu interativo
```

### Opção 2: Manual (Controle total)
```bash
# Ler passo-a-passo
cat NANO_PASSO_A_PASSO.md

# Seguir cada comando
```

### Opção 3: Copiar/Colar (Mais rápido)
```bash
# Abrir file
cat NANO_CHEATSHEET.sh

# Copiar comandos e executar
```

---

## 📊 Matriz de Decisão

| Situação | Arquivo | Ação |
|----------|---------|------|
| Primeira vez | PASSO_A_PASSO | Ler tudo |
| Precisa entender | TUTORIAL | Ler seção relevante |
| Sabe o que faz | CHEATSHEET | Copy/paste |
| Quer fácil | setup-nano.sh | ./script |
| Problemas? | TUTORIAL | Ver troubleshooting |
| Apresentação iminente | PASSO_A_PASSO | Revisar e praticar |

---

## ⏱️ Tempo Estimado

| Atividade | Tempo | Arquivo |
|-----------|-------|---------|
| Ler guia completo | 15 min | TUTORIAL |
| Ler passo-a-passo | 10 min | PASSO_A_PASSO |
| Executar tudo | 45 min | CHEATSHEET ou setup-nano.sh |
| Consultar rápido | 2 min | CHEATSHEET |

---

## 📞 Referência de Conteúdo

### Precisa de qual info?

#### Como conectar no Nano?
- PASSO_A_PASSO.md - PASSO 1
- TUTORIAL.md - PARTE 1
- CHEATSHEET.sh - Linha 3-6

#### Como fazer build?
- PASSO_A_PASSO.md - PASSO 2
- TUTORIAL.md - PARTE 2
- CHEATSHEET.sh - Linha 12-20

#### Como rodar API?
- PASSO_A_PASSO.md - PASSO 4
- TUTORIAL.md - PARTE 3
- CHEATSHEET.sh - Linha 27-40

#### Como testar?
- PASSO_A_PASSO.md - PASSO 5
- TUTORIAL.md - PARTE 4
- CHEATSHEET.sh - Linha 47-59

#### Ocorreu um erro!
- PASSO_A_PASSO.md - "Se Algo Der Errado"
- TUTORIAL.md - PARTE 7
- CHEATSHEET.sh - Debug section

---

## 💾 Estrutura de Diretórios

```
backend_tcc_mvp/
├─ NANO_PASSO_A_PASSO.md      ← Comece aqui
├─ NANO_TUTORIAL.md           ← Explicações completas
├─ NANO_CHEATSHEET.sh         ← Comandos rápidos
├─ setup-nano.sh              ← Menu interativo
│
├─ docker-compose-nano.yml    ← Configuração Docker
├─ docker/
│  └─ Dockerfile.jetson-nano  ← Imagem Docker
│
├─ app/                        ← Código da API
├─ data/                       ← Dados pra testar
└─ ...
```

---

## 🎯 Roteiro Sugerido (TCC)

### 1º dia: Preparação (30 min)
1. Ler `NANO_PASSO_A_PASSO.md` 
2. Ler `NANO_TUTORIAL.md` (troubleshooting)

### 2º dia: Build (2 horas include espera)
1. PASSO 1-3 (`setup-nano.sh --build` ou manual)

### 2º dia: Teste (15 min)
1. PASSO 4-7 (`setup-nano.sh --run`)
2. Capturar screenshots

### 3º dia: Prática (30 min antes da apresentação)
1. Executar tudo novamente
2. Verificar checklist
3. Ter backup pronto

---

## ✅ Antes de Apresentar

1. ✓ Leu passo-a-passo?
2. ✓ Executou tudo uma vez?
3. ✓ Capturou screenshots?
4. ✓ Testou no dia anterior?
5. ✓ Tem plano B (vídeo)?
6. ✓ Nano está ligada?
7. ✓ SSH funciona (`ssh jetson`)?
8. ✓ Documentação aberta ou impressa?

---

## 📱 No Dia da Apresentação

```bash
# De manhã
ssh jetson

# Verificar sistema
jetson_release

# Verificar docker
docker images | grep ar-diagnostic

# Estar pronto
cd ~/backend_tcc_mvp
docker compose -f docker-compose-nano.yml up

# Enquanto apresenta
# - Abrir Swagger (http://jetson:8000/docs)
# - Fazer requisição
# - Explicar latência
# - Mostrar screenshots
# - Reproduzir resultado
```

---

## 📞 SOS - Ajuda Rápida

| Problema | Solução | Arquivo |
|----------|---------|---------|
| Docker não instalado | Instalar manual | TUTORIAL 7.1 |
| Build falha | Ver memória/swap | CHEATSHEET cleanup |
| API não responde | Ver logs | CHEATSHEET logs |
| CUDA error | Reiniciar Nano | TUTORIAL 7.3 |
| Lento demais | Normal pro Nano | PASSO_A_PASSO dicas |

---

## 🆘 Não Funciona?

```bash
# 1. Reconectar
ssh jetson

# 2. Verificar hardware
jetson_release

# 3. Verificar docker
docker --version

# 4. Ver logs
docker logs ar-api-nano

# 5. Se tudo falhar
ssh jetson "docker system prune -f --all"
# Recomeçar do PASSO 2
```

---

## 📝 Ficou com dúvida?

1. **Geral** → NANO_PASSO_A_PASSO.md
2. **Específico** → NANO_TUTORIAL.md
3. **Rápido** → NANO_CHEATSHEET.sh
4. **Fácil** → setup-nano.sh

**Nessa ordem! 👆**

---

**Última atualização:** 2026-04-10  
**Status:** Completo e testado ✓
