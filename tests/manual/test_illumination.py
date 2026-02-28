"""
Teste manual de iluminação
Uso: python tests/manual/test_illumination.py 
ou
poetry run python tests/manual/test_illumination.py
"""
import cv2
from pathlib import Path
from app.pdi.illumination import IlluminationAnalyzer
from app.config.config import Config

def main():
    # Testa com imagem de exemplo
    test_images = [
        "data/illumination/bright_overexposed/bright_image1.jpg",
        "data/illumination/bright_overexposed/bright_image2.jpg",
        "data/illumination/bright_overexposed/bright_image3.jpg",
        "data/illumination/bright_overexposed/bright_image4.jpg",
        "data/illumination/bright_overexposed/bright_image5.jpg",
        "data/illumination/dark_underexposed/dark_image1.jpg",
        "data/illumination/dark_underexposed/dark_image2.jpg",
        "data/illumination/dark_underexposed/dark_image3.jpg",
        "data/illumination/dark_underexposed/dark_image4.jpg",
        "data/illumination/dark_underexposed/dark_image5.jpg",
        "data/illumination/normal/normal_image1.jpg",
        "data/illumination/normal/normal_image2.jpg",
        "data/illumination/normal/normal_image3.jpg",
        "data/illumination/normal/normal_image4.jpg",
        "data/illumination/normal/normal_image5.jpg"
    ]
    
    # Carrega config do YAML
    config_dict = Config().get_all()
    analyzer = IlluminationAnalyzer(config=config_dict)
    
    print("\n" + "="*60)
    print("Teste Manual - IlluminationAnalyzer")
    print("="*60)
    
    for img_path in test_images:
        path = Path(img_path)
        if not path.exists():
            print(f"\n  {img_path} - NÃO ENCONTRADA")
            continue
        
        image = cv2.imread(str(path))
        if image is None:
            print(f"\n {img_path} - ERRO AO LER")
            continue
        
        score, details = analyzer.analyze(image)
        
        print(f"\nImagem: {img_path}")
        print(f"   Score: {score:.3f}")
        print(f"   Label: {details.get('label', 'N/A')}")
        print(f"   Brilho médio (luma): {details.get('mean_luma', 0):.1f}")
        print(f"   Contraste (std): {details.get('std_luma', 0):.1f}")
        print(f"   Clipping escuro: {details.get('pct_clipped_dark', 0):.2%}")
        print(f"   Clipping claro: {details.get('pct_clipped_bright', 0):.2%}")
        print(f"   Uniformidade: {details.get('uniformity', 'N/A'):.3f}")
        print(f"   Score exposição: {details.get('exposure_score', 'N/A'):.3f}")
        print(f"   Score contraste: {details.get('contrast_score', 'N/A'):.3f}")
        print(f"   Penalização por clipping: {details.get('clipping_penalty', 'N/A'):.3f}")
        
        # Status baseado no label
        label = details.get('label', 'unknown')
        status_map = {
            'adequate': 'ILUMINAÇÃO ADEQUADA',
            'acceptable': 'ILUMINAÇÃO ACEITÁVEL',
            'underexposed': 'SUBEXPOSTA (escura demais)',
            'overexposed': 'SUPEREXPOSTA (estourada)',
            'poor': 'ILUMINAÇÃO RUIM'
        }
        status = status_map.get(label, 'DESCONHECIDA')
        print(f"   Status: {status} [{label}]")
        print("="*60)

#------------------------------------------------------------------------------------------------------------------------------------------------------------------------
if __name__ == "__main__":
    main()
