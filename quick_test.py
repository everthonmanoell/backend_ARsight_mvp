import cv2, time
from PIL import Image
from app.pipeline.illumination_pipeline import IlluminationPipeline

pipeline = IlluminationPipeline(model_type='qwen', use_4bit=True, device='cuda')
img = cv2.imread('data/illumination/normal/normal_image1.jpg')
img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
pil_img = Image.fromarray(img_rgb)

# Primeira chamada (inclui carregamento)
start = time.time()
result = pipeline.diagnose(pil_img)
t1 = time.time() - start
print(f'\n1ª chamada (com carregamento): {t1:.2f}s')

# Segunda chamada (modelo já carregado)
start = time.time()
result = pipeline.diagnose(pil_img)
t2 = time.time() - start  
print(f'2ª chamada (sem carregamento): {t2:.2f}s')
print(f'\nExplicação: {result["explanation"]}')
