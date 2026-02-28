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
    
    def __init__(self, model_type: str = 'qwen', use_4bit: bool = True, device: str = 'cuda', enable_compile: bool = False):
        """
        Inicializa pipeline
        
        Args:
            model_type: 'qwen' ou 'phi'
            use_4bit: Usar quantização 4-bit
            device: 'cuda', 'cpu', ou 'auto'
            enable_compile: Usar torch.compile() para otimização (requer PyTorch 2.0+)
        """
        self.model_type = model_type
        self.use_4bit = use_4bit
        self.device = device
        self.enable_compile = enable_compile
        
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
                self.model = QwenARModel(use_4bit=self.use_4bit, device=self.device, enable_compile=self.enable_compile)
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
    
    def extract_metrics_batch(self, images: list) -> list:
        """
        Extrai métricas de múltiplas imagens em batch
        
        Args:
            images: Lista de imagens PIL
        
        Returns:
            Lista de dicionários com métricas
        """
        logger.info(f"Extracting metrics from {len(images)} images...")
        
        all_metrics = []
        for idx, image in enumerate(images, 1):
            logger.debug(f"  Processing image {idx}/{len(images)}")
            metrics = self.extract_metrics(image)
            all_metrics.append(metrics)
        
        logger.info(f"Extracted metrics from {len(all_metrics)} images")
        return all_metrics
    
    def diagnose_from_metrics(self, metrics: Dict) -> Dict:
        """
        Diagnostica usando métricas pré-calculadas (sem processar imagem)
        
        Args:
            metrics: Dicionário com métricas já extraídas
        
        Returns:
            Diagnóstico completo
        """
        logger.info(f"Diagnosing from pre-calculated metrics: {metrics.get('illumination_label')}")
        
        # Carrega modelo se necessário
        self._load_model()
        
        # Diagnóstico com SLM
        result = self.model.diagnose(metrics)
        
        return result
    
    def diagnose_from_metrics_batch(self, metrics_list: list) -> list:
        """
        Diagnostica múltiplas cenas usando métricas pré-calculadas
        Processa em batch para maior eficiência
        
        Args:
            metrics_list: Lista de dicionários com métricas
        
        Returns:
            Lista de diagnósticos
        """
        logger.info(f"Batch diagnosis for {len(metrics_list)} scenes...")
        
        # Carrega modelo se necessário
        self._load_model()
        
        # Processa em batch (se modelo suportar)
        if hasattr(self.model, 'diagnose_batch'):
            logger.info("Using model batch processing")
            results = self.model.diagnose_batch(metrics_list)
        else:
            # Fallback: processa sequencialmente
            logger.info("Model doesn't support batch, processing sequentially")
            results = []
            for idx, metrics in enumerate(metrics_list, 1):
                logger.debug(f"  Processing scene {idx}/{len(metrics_list)}")
                result = self.model.diagnose(metrics)
                results.append(result)
        
        logger.info(f"Completed batch diagnosis for {len(results)} scenes")
        return results
    
    def diagnose_images_batch(self, image_paths: list) -> list:
        """
        Diagnostica múltiplas imagens a partir de caminhos de arquivo
        Extrai métricas + diagnóstico em batch para máxima eficiência
        
        Args:
            image_paths: Lista de caminhos de arquivos de imagens
        
        Returns:
            Lista de diagnósticos completos
        """
        logger.info(f"Processing {len(image_paths)} images in batch...")
        
        # 1. Carrega imagens
        images = []
        for path in image_paths:
            img = Image.open(path)
            images.append(img)
        
        # 2. Extrai métricas em batch
        metrics_list = self.extract_metrics_batch(images)
        
        # 3. Diagnostica em batch
        results = self.diagnose_from_metrics_batch(metrics_list)
        
        logger.info(f"Completed batch processing for {len(results)} images")
        return results
