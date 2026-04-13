# Dados de Entrada para Benchmarks

Imagens e datasets usados para testar performance.

## 📁 Estrutura

```
data/
├── README.md           ← Você está aqui
└── images/            
    ├── batch1/        ← Imagens do batch 1
    ├── batch2/        ← Imagens do batch 2
    ├── batch3/        ← Imagens do batch 3
    └── ...
```

---

## 🖼️ Como Organizar Imagens

### Criar novo batch

```bash
cd data/images/

# Criar pasta
mkdir batch1

# Copiar imagens (10-20 imagens por batch recomendado)
cp ~/suas_imagens/*.jpg batch1/

# Verificar
ls -la batch1/
```

### Estrutura recomendada

Para cada batch, ter ~10 imagens:
- 3-4 com iluminação adequada
- 3-4 subexpostas (escuras)
- 3-4 superexpostas (claras)

Exemplo:
```
batch1/
├── normal_001.jpg      ← Iluminação adequada
├── normal_002.jpg
├── normal_003.jpg
├── dark_001.jpg        ← Subexposto
├── dark_002.jpg
├── dark_003.jpg
├── bright_001.jpg      ← Superexposto
├── bright_002.jpg
├── bright_003.jpg
└── mixed_001.jpg       ← Misto
```

---

## 📊 Usar Dados Existentes

Se já tem imagens em outro lugar:

```bash
# Opção 1: Copiar
cp -r ~/seu/diretório/imagens/* data/images/batch1/

# Opção 2: Link simbólico (não copia, apenas refere)
ln -s ~/seu/diretório/imagens data/images/batch1

# Verificar
ls data/images/batch1/
```

---

## 🎯 Fonte Recomendada de Imagens

### Para Benchmarks, usar imagens de:

1. **Seu próprio dataset de testes** (ideal)
   ```bash
   data/illumination/  # Se existir da aplicação
   ```

2. **Gerar sintéticas** (rápido)
   ```python
   from PIL import Image
   import os
   
   # Criar imagens de teste
   for i in range(10):
       img = Image.new('RGB', (1920, 1080), color=(128, 128, 128))
       img.save(f'data/images/batch1/test_{i:03d}.jpg')
   ```

3. **Webcam/câmera** (mais realista)
   ```bash
   # Capturar 10 fotos da webcam
   # e salvar em data/images/batch1/
   ```

---

## 🔄 Fluxo de Teste

### Quando rodar benchmark:

```bash
# 1. Ter imagens em data/images/batch1/
ls data/images/batch1/  # verificar

# 2. Script de benchmark lê de lá
python scripts/benchmark_jetson_vs_legion.py \
  --images-dir data/images/batch1/

# 3. Resultados salvos em outputs/
# outputs/comparison/runs_raw.csv (referencia imagens mas não copia)
```

---

## 💾 Formato de Imagens Suportado

- **JPEG** (.jpg, .jpeg) ✅ Recomendado
- **PNG** (.png) ✅ Suportado
- **BMP** (.bmp) ✅ Suportado
- **TIFF** (.tiff) ⚠️ Suportado com ressalvas

**Tamanho recomendado:** 
- 1920x1080 (Full HD)
- 1280x720 (HD)
- Até 10MB por imagem

---

## 🗑️ Limpeza

### Remover dados antigos

```bash
rm -rf data/images/batch_antigo/
```

### Começar do zero

```bash
rm -rf data/images/*
mkdir data/images/batch1
# Copie novos dados
```

---

## 📝 Nomeação de Imagens

**Convenção recomendada:**

```
{condição}_{sequência}.jpg

Exemplos:
- normal_001.jpg
- dark_001.jpg
- bright_001.jpg
- mixed_001.jpg
- corrupted_001.jpg
```

Isso facilita análise depois!

---

## 🔍 Verificar Dados

```bash
# Contar imagens por batch
ls data/images/batch*/  | wc -l

# Verificar tamanho total
du -sh data/images/

# Listar com tamanho
ls -lh data/images/batch1/
```

---

## 📍 Próximos Passos

- [ ] Criar `batch1/`, `batch2/`, `batch3/`
- [ ] Adicionar ~10 imagens por batch
- [ ] Verificar com `ls data/images/batch1/`
- [ ] Rodar benchmark (ver BENCHMARK_QUICK_REFERENCE.sh)

---

**Última atualização:** 2026-04-13
