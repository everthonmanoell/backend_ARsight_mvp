"""Benchmark separando análise PDI vs LLM"""
import cv2, time
from PIL import Image
from app.pdi.illumination import IlluminationAnalyzer
from app.pipeline.illumination_pipeline import IlluminationPipeline
from app.config.config import Config

# Carrega imagem
img = cv2.imread('data/illumination/normal/normal_image1.jpg')
img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
pil_img = Image.fromarray(img_rgb)

# 1. Teste só análise PDI
print("\n=== ANÁLISE PDI APENAS ===")
config = Config().get_all()
analyzer = IlluminationAnalyzer(config=config)

times = []
for i in range(5):
    start = time.time()
    score, details = analyzer.analyze(img)
    elapsed = time.time() - start
    times.append(elapsed)
    print(f"Run {i+1}: {elapsed*1000:.1f}ms")

print(f"Média PDI: {sum(times)/len(times)*1000:.1f}ms\n")

# 2. Teste pipeline completo
print("=== PIPELINE COMPLETO ===")
pipeline = IlluminationPipeline(model_type='qwen', use_4bit=True, device='cuda')

# Primeira chamada (com carregamento)
start = time.time()
result = pipeline.diagnose(pil_img)
t1 = time.time() - start
print(f"1ª chamada (com carregamento modelo): {t1:.2f}s")

# Segunda chamada (modelo quente)
start = time.time()
result = pipeline.diagnose(pil_img)
t2 = time.time() - start
print(f"2ª chamada (modelo quente): {t2:.2f}s")

print(f"\n=== BREAKDOWN ===")
print(f"PDI: ~{sum(times)/len(times):.3f}s")
print(f"LLM: ~{t2 - sum(times)/len(times):.2f}s")
print(f"Total: ~{t2:.2f}s")
