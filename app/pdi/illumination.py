"""
Illumination Analysis
Análise de iluminação da cena
"""
import logging
import cv2
import numpy as np

logger = logging.getLogger(__name__)


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

    def analyze(self, image: np.ndarray) -> tuple[float, dict]:
        """
        Analisa imagem e retorna score + detalhes
        
        Args:
            image: Imagem BGR (numpy array)
            
        Returns:
            tuple: (score, details)
                - score: qualidade 0-1
                - details: métricas detalhadas
        """
        if image is None or image.size == 0:
            return 0.0, {
                "mean_luma": 0.0,
                "std_luma": 0.0,
                "uniformity": 0.0,
                "pct_clipped_dark": 1.0,
                "pct_clipped_bright": 1.0,
            }

        try:
            # Luminância (Y) do espaço YCrCb
            y = cv2.cvtColor(image, cv2.COLOR_BGR2YCrCb)[:, :, 0]

            mean_luma = float(np.mean(y))
            std_luma = float(np.std(y))

            # Uniformidade via coeficiente de variação
            cv_luma = std_luma / (mean_luma + 1e-6)
            uniformity = float(1.0 / (1.0 + cv_luma))

            # Clipping (perda de detalhe)
            pct_dark = float(np.mean(y < 10))
            pct_bright = float(np.mean(y > 245))

            # Exposição (ideal = 128)
            target = 128.0
            exposure_score = 1.0 - min(abs(mean_luma - target) / target, 1.0)

            # Contraste
            contrast_score = min(std_luma / 96.0, 1.0)

            # Penalização por clipping
            clipping_penalty = min(pct_dark + pct_bright, 1.0)

            # Score final combinado
            score = (0.60 * exposure_score) + (0.30 * contrast_score) + (0.10 * uniformity)
            score *= (1.0 - 0.7 * clipping_penalty)
            score = float(np.clip(score, 0.0, 1.0))

            details = {
                "mean_luma": mean_luma,
                "std_luma": std_luma,
                "uniformity": uniformity,
                "pct_clipped_dark": pct_dark,
                "pct_clipped_bright": pct_bright,
                "exposure_score": float(exposure_score),
                "contrast_score": float(contrast_score),
                "clipping_penalty": float(clipping_penalty),
            }
            
            # Classifica condição
            details['label'] = self.classify(details, score)

            return score, details

        except Exception as e:
            logger.error(f"Error analyzing illumination: {e}")
            return 0.5, {"error": str(e)}
        
    def classify(self, details: dict, score: float) -> str:
        """
        Classifica condição de iluminação
        
        Args:
            details: Detalhes da análise
            score: Score de qualidade (0-1)
        
        Returns:
            Label: "underexposed", "adequate", "acceptable", "overexposed", "poor"
        """
        illum_cfg = self.config.get("pdi", {}).get("illumination", {})
        
        # Gates de clipping
        clipped_bright_thr = float(illum_cfg.get("clipped_bright_overexposed", 0.10))
        clipped_dark_thr = float(illum_cfg.get("clipped_dark_underexposed", 0.10))
        
        # Thresholds de luminância
        mean_under_thr = float(illum_cfg.get("mean_underexposed", 70))
        mean_over_thr = float(illum_cfg.get("mean_overexposed", 185))
        
        # Thresholds de score
        good_thr = float(illum_cfg.get("good", 0.7))
        min_acc_thr = float(illum_cfg.get("min_acceptable", 0.5))
        
        pct_bright = float(details.get("pct_clipped_bright", 0.0))
        pct_dark = float(details.get("pct_clipped_dark", 0.0))
        mean_luma = float(details.get("mean_luma", 128.0))
        
        # Gates fortes (prioridade)
        if pct_bright >= clipped_bright_thr or mean_luma >= mean_over_thr:
            return "overexposed"
        if pct_dark >= clipped_dark_thr or mean_luma <= mean_under_thr:
            return "underexposed"
        
        # Decide por score
        if score >= good_thr:
            return "adequate"
        if score >= min_acc_thr:
            return "acceptable"
        
        return "poor"
    
    def is_well_lit(self, image: np.ndarray, threshold: float = 0.7) -> bool:
        """Verifica se cena está bem iluminada"""
        score, _ = self.analyze(image)
        return score >= threshold
