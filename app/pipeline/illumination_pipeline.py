"""
Illumination Pipeline - MVP
Orquestra análise de iluminação + SLM
"""

import logging
from PIL import Image
import numpy as np
import cv2
from typing import Dict

from app.pdi.illumination import IlluminationAnalyzer
from app.models.qwen_model import QwenARModel
from app.models.phi_model import PhiARModel
from app.config.config import Config

logger = logging.getLogger(__name__)


class IlluminationPipeline:
    """
    Pipeline simplificado para diagnóstico de iluminação
    """
    
    def __init__(self, model_type: str = 'qwen', use_4bit: bool = True, device: str = 'cuda'):
        """
        Inicializa pipeline
        
        Args:
            model_type: 'qwen' ou 'phi'
            use_4bit: Usar quantização 4-bit
            device: 'cuda', 'cpu', ou 'auto'
        """
        self.model_type = model_type
        self.use_4bit = use_4bit
        self.device = device
        
        # Carrega configurações
        config = Config()
        self.config_dict = config.get_all()
        
        # Inicializa componentes
        logger.info("Initializing Illumination Pipeline...")
        
        # Analisador de iluminação
        self.illumination_analyzer = IlluminationAnalyzer(config=self.config_dict)
        logger.info("- Illumination analyzer loaded")
        
        # Modelo SLM (lazy loading - só carrega no primeiro diagnose)
        self.model = None
        logger.info(f"- Model ({model_type}) will be loaded on first inference")
        
        logger.info("Pipeline initialized successfully!")
    
    def _load_model(self):
        """Carrega modelo SLM (lazy loading)"""
        if self.model is None:
            logger.info(f"Loading {self.model_type} model...")
            
            if self.model_type == 'qwen':
                self.model = QwenARModel(use_4bit=self.use_4bit, device=self.device)
            elif self.model_type == 'phi':
                self.model = PhiARModel(use_4bit=self.use_4bit, device=self.device)
            else:
                raise ValueError(f"Unknown model type: {self.model_type}")
            
            logger.info("Model loaded successfully!")
    
    def diagnose(self, image: Image.Image) -> Dict:
        """
        Diagnostica imagem individual
        
        Args:
            image: Imagem PIL
        
        Returns:
            Diagnóstico completo
        """
        # Converte PIL para OpenCV
        image_np = np.array(image)
        if len(image_np.shape) == 2:  # Grayscale
            image_np = cv2.cvtColor(image_np, cv2.COLOR_GRAY2BGR)
        elif image_np.shape[2] == 4:  # RGBA
            image_np = cv2.cvtColor(image_np, cv2.COLOR_RGBA2BGR)
        else:  # RGB
            image_np = cv2.cvtColor(image_np, cv2.COLOR_RGB2BGR)
        
        logger.info("Extracting illumination metrics...")
        
        # Analisa iluminação
        illumination_score, illumination_details = self.illumination_analyzer.analyze(image_np)
        
        # Monta métricas
        metrics = {
            'illumination': illumination_score,
            'illumination_label': illumination_details.get('label', 'unknown'),
            'mean_luma': illumination_details.get('mean_luma', 0.0),
            'std_luma': illumination_details.get('std_luma', 0.0),
            'uniformity': illumination_details.get('uniformity', 0.0),
            'pct_clipped_dark': illumination_details.get('pct_clipped_dark', 0.0),
            'pct_clipped_bright': illumination_details.get('pct_clipped_bright', 0.0)
        }
        
        logger.info(f"Illumination: {metrics['illumination_label']} (score: {illumination_score:.3f})")
        
        # Carrega modelo se necessário
        self._load_model()
        
        # Diagnóstico com SLM
        logger.info("Running SLM diagnosis...")
        result = self.model.diagnose(metrics)
        
        # Adiciona detalhes de iluminação
        result['illumination_details'] = illumination_details
        
        return result
    
    def extract_metrics(self, image: Image.Image) -> Dict:
        """
        Extrai apenas métricas de iluminação (sem LLM)
        
        Args:
            image: Imagem PIL
        
        Returns:
            Dicionário com métricas
        """
        # Converte PIL para OpenCV
        image_np = np.array(image)
        if len(image_np.shape) == 2:  # Grayscale
            image_np = cv2.cvtColor(image_np, cv2.COLOR_GRAY2BGR)
        elif image_np.shape[2] == 4:  # RGBA
            image_np = cv2.cvtColor(image_np, cv2.COLOR_RGBA2BGR)
        else:  # RGB
            image_np = cv2.cvtColor(image_np, cv2.COLOR_RGB2BGR)
        
        logger.info("Extracting illumination metrics (no LLM)...")
        
        # Analisa iluminação
        illumination_score, illumination_details = self.illumination_analyzer.analyze(image_np)
        
        # Retorna métricas
        metrics = {
            'illumination': illumination_score,
            'illumination_label': illumination_details.get('label', 'unknown'),
            'mean_luma': illumination_details.get('mean_luma', 0.0),
            'std_luma': illumination_details.get('std_luma', 0.0),
            'uniformity': illumination_details.get('uniformity', 0.0),
            'pct_clipped_dark': illumination_details.get('pct_clipped_dark', 0.0),
            'pct_clipped_bright': illumination_details.get('pct_clipped_bright', 0.0)
        }
        
        logger.info(f"Illumination: {metrics['illumination_label']} (score: {illumination_score:.3f})")
        
        return metrics
