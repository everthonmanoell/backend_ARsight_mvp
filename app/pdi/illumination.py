"""
Illumination Analysis
Análise de iluminação da cena
"""
import logging
import cv2
import numpy as np

# configura logger para este módulo, serve para obter logs específicos do ROIExtractor, sem poluir outros módulos
logger = logging.getLogger(__name__)

# IlluminationAnalyzer é responsável por analisar a qualidade da iluminação da cena, retornando um score e detalhes para auditoria
class IlluminationAnalyzer:
    """
    Analisa qualidade da iluminação na cena.
    Retorna um score [0,1] + features para auditoria.
    """
    
    def __init__(self, config: dict = None):
        """
        Inicializa analisador de iluminação
        
        Args:
            config: Configuração completa (thresholds.yaml)
        """
        self.config = config or {}

    #------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    # método que analisa a imagem e retorna score + detalhes
    def analyze(self, image: np.ndarray) -> tuple[float, dict]:
        # Verifica se a imagem é válida, se não for, retorna score zero e detalhes vazios
        if image is None or image.size == 0:
            return 0.0, {
                "mean_luma": 0.0,
                "std_luma": 0.0,
                "uniformity": 0.0,
                "pct_clipped_dark": 1.0,
                "pct_clipped_bright": 1.0,
            }

        try:
            # Luminância (Y) do espaço YCrCb é uma boa medida de brilho da cena
            y = cv2.cvtColor(image, cv2.COLOR_BGR2YCrCb)[:, :, 0]

            mean_luma = float(np.mean(y)) # Brilho médio da cena (varia no range de 0 a 255)
            std_luma = float(np.std(y))   # Contraste da cena (variação de brilho, varia de 0 a ~64 para cenas normais)

            # Uniformidade via coeficiente de variação
            # Uniformidade é importante para tracking AR, pois iluminação desigual pode causar falhas
            cv_luma = std_luma / (mean_luma + 1e-6)   # Evita divisão por zero
            uniformity = float(1.0 / (1.0 + cv_luma)) # Normaliza para [0,1], onde 1 é perfeitamente uniforme

            # Clipping (perda de detalhe em sombras/altos)
            pct_dark = float(np.mean(y < 10))     # Proporção de pixels muito escuros (clipping em sombras)
            pct_bright = float(np.mean(y > 245))  # Proporção de pixels muito claros (clipping em altos)

            # Exposição
            # assume que ideal é ter brilho médio em torno de 128 (meio-termo)
            target = 128.0

            # Score de exposição baseado na distância do brilho médio ao valor ideal
            # esse score varia de 0 (muito subexposto ou superexposto) a 1 (perfeitamente exposto)
            exposure_score = 1.0 - min(abs(mean_luma - target) / target, 1.0) 

            # Contraste
            # desvio padrão baixo indica baixa textura (no intervalo de 0 a 64, onde 64 é um contraste forte)
            # desvio padrão alto indica boa textura(ou seja, bom para tracking)
            # AJUSTADO: de 64 para 96 para não saturar tão rápido
            contrast_score = min(std_luma / 96.0, 1.0)

            # Penalização por clipping
            # clipping significa que partes da cena estão perdendo detalhes, o que é ruim para tracking AR
            # clipping_penalty é uma penalização combinada para pixels muito escuros ou muito claros
            clipping_penalty = min(pct_dark + pct_bright, 1.0) 

            # Score final é calculado combinando exposição, contraste e uniformidade, com penalização por clipping
            score = (0.60 * exposure_score) + (0.30 * contrast_score) + (0.10 * uniformity)
            score *= (1.0 - 0.7 * clipping_penalty)  # penaliza forte se clipar
            score = float(np.clip(score, 0.0, 1.0))  # Normaliza para [0,1]

            details = {
                "mean_luma": mean_luma,                         # Brilho médio da cena
                "std_luma": std_luma,                           # Contraste da cena (variação de brilho)
                "uniformity": uniformity,                       # Uniformidade da iluminação (1.0 = perfeita, 0.0 = muito desigual)
                "pct_clipped_dark": pct_dark,                   # Proporção de pixels muito escuros (clipping em sombras)
                "pct_clipped_bright": pct_bright,               # Proporção de pixels muito claros (clipping em altos)
                "exposure_score": float(exposure_score),        # Score de exposição (0.0-1.0, onde 1.0 é ideal)
                "contrast_score": float(contrast_score),        # Score de contraste (0.0-1.0, onde 1.0 é alto contraste)
                "clipping_penalty": float(clipping_penalty),    # Penalização por clipping (0.0 = sem clipping, 1.0 = clipping total)
            }
            
            # Classifica condição baseada em gates configuráveis
            details['label'] = self.classify(details, score)

            return score, details

        except Exception as e:
            logger.error(f"Error analyzing illumination: {e}")
            return 0.5, {"error": str(e)}
        
   #------------------------------------------------------------------------------------------------------------------------------------------------------------------------
   # método para classificar a condição de iluminação baseado em gates configuráveis, usando tanto os detalhes calculados quanto o score final 
    def classify(self, details: dict, score: float) -> str:
        """
        Classifica condição de iluminação baseado em gates configuráveis
        
        Args:
            details: Detalhes da análise
            score: Score de qualidade (0-1)
        
        Returns:
            Label: "underexposed", "adequate", "acceptable", "overexposed", "poor"
        """
        illum_cfg = self.config.get("pdi", {}).get("illumination", {})
        
        # Gates de clipping (mais confiáveis)
        clipped_bright_thr = float(illum_cfg.get("clipped_bright_overexposed", 0.10))
        clipped_dark_thr = float(illum_cfg.get("clipped_dark_underexposed", 0.10))
        
        # Thresholds de luminância (fallback)
        mean_under_thr = float(illum_cfg.get("mean_underexposed", 70))
        mean_over_thr = float(illum_cfg.get("mean_overexposed", 185))
        
        # Thresholds de score
        good_thr = float(illum_cfg.get("good", 0.7))
        min_acc_thr = float(illum_cfg.get("min_acceptable", 0.5))
        
        pct_bright = float(details.get("pct_clipped_bright", 0.0))
        pct_dark = float(details.get("pct_clipped_dark", 0.0))
        mean_luma = float(details.get("mean_luma", 128.0))
        
        # Gates fortes (mais confiáveis) - prioridade
        if pct_bright >= clipped_bright_thr or mean_luma >= mean_over_thr:
            return "overexposed"
        if pct_dark >= clipped_dark_thr or mean_luma <= mean_under_thr:
            return "underexposed"
        
        # Caso "normal": decide por score
        if score >= good_thr:
            return "adequate"
        if score >= min_acc_thr:
            return "acceptable"
        
        return "poor"
    
    #------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    # método auxiliar para verificar se a cena está bem iluminada com base em um limiar de score
    def is_well_lit(self, image: np.ndarray, threshold: float = 0.7) -> bool:
        score, _ = self.analyze(image)
        return score >= threshold
