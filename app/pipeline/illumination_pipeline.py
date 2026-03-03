"""
Illumination Pipeline - MVP
Orquestra análise de iluminação + SLM
"""

import logging
from PIL import Image
from typing import Dict

from app.pdi.illumination import IlluminationAnalyzer
from app.models.qwen_model import QwenARModel
from app.models.phi_model import PhiARModel
from app.config.config import Config

# configura logger para este módulo
logger = logging.getLogger(__name__)

#------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# classe principal do pipeline de diagnóstico de iluminação, responsável por orquestrar a análise de iluminação e o modelo SLM para fornecer diagnósticos completos
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

        # Armazena configurações de modelo e dispositivo para uso posterior
        self.model_type = model_type
        self.use_4bit = use_4bit
        self.device = device
        
        # Carrega configurações do arquivo YAML
        config = Config()
        self.config_dict = config.get_all()
        
        # Inicializa componentes
        logger.info("Initializing Illumination Pipeline...")
        self.illumination_analyzer = IlluminationAnalyzer(config=self.config_dict) # analisador de iluminação
        logger.info("- Illumination analyzer loaded")
        
        # Modelo SLM (lazy loading - só carrega no primeiro diagnose durante warmup para otimizar tempo de startup)
        self.model = None

        logger.info(f"- Model ({model_type}) will be loaded on first inference")
        
        logger.info("Pipeline initialized successfully!")

#------------------------------------------------------------------------------------------------------------------------------------------------------------------------   
    # método para carregar o modelo SLM de forma preguiçosa (lazy loading), otimizando o tempo de inicialização do pipeline
    def _load_model(self):
        """Carrega modelo SLM (lazy loading), garantindo que o modelo só seja carregado quando necessário"""

        # verificar se o modelo já foi carregado para evitar recarregamentos desnecessários
        if self.model is None:
            logger.info(f"Loading {self.model_type} model...")
            
            # carrega o modelo SLM especificado nas configurações, usando quantização 4-bit se configurado, e alocando no dispositivo correto (GPU ou CPU)
            if self.model_type == 'qwen':
                self.model = QwenARModel(use_4bit=self.use_4bit, device=self.device)
            elif self.model_type == 'phi':
                self.model = PhiARModel(use_4bit=self.use_4bit, device=self.device)
            else:
                raise ValueError(f"Unknown model type: {self.model_type}")
            
            logger.info("Model loaded successfully!")

#------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    # método privado para extrair métricas de iluminação a partir de uma imagem
    def _extract_metrics(self, image: Image.Image) -> tuple:
        """
        Extrai métricas de iluminação. Retorna (metrics, illumination_details).
        """
        illumination_score, illumination_details = self.illumination_analyzer.analyze(image)

        metrics = {
            'illumination':       illumination_score,
            'illumination_label': illumination_details.get('label', 'unknown'),
            'mean_luma':          illumination_details.get('mean_luma', 0.0),
            'std_luma':           illumination_details.get('std_luma', 0.0),
            'uniformity':         illumination_details.get('uniformity', 0.0),
            'pct_clipped_dark':   illumination_details.get('pct_clipped_dark', 0.0),
            'pct_clipped_bright': illumination_details.get('pct_clipped_bright', 0.0)
        }

        logger.debug(f"Illumination: {metrics['illumination_label']} (score: {illumination_score:.3f})")

        return metrics, illumination_details

#------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    # thin wrapper sobre o IlluminationAnalyzer — extrai métricas de uma lista de imagens PIL
    # necessário para o padrão 2-step da API (PDI separado do SLM para isolamento de erros por frame)
    def extract_metrics_batch(self, images: list) -> list:
        """
        Extrai métricas de iluminação de uma lista de imagens PIL.
        Retorna lista de dicts de métricas (sem diagnóstico SLM).
        """
        logger.info(f"Extracting PDI metrics for {len(images)} images...")
        metrics_list = []
        for idx, image in enumerate(images, 1):
            logger.debug(f"  Extracting metrics {idx}/{len(images)}")
            metrics, _ = self._extract_metrics(image)
            metrics_list.append(metrics)
        return metrics_list

#------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    def diagnose_from_metrics_batch_with_summary(self, metrics_list: list):
        """
        Diagnostica N cenas + gera summary do ambiente num unico batch SLM (N+1 prompts).

        Args:
            metrics_list: Lista de dicionários com métricas PDI

        Returns:
            tuple (individual_results: List[Dict], summary: Dict)
        """
        logger.info(f"Batch+summary diagnosis for {len(metrics_list)} scenes...")
        self._load_model()
        results, summary = self.model.diagnose_batch_with_summary(metrics_list)
        logger.info("Batch+summary completed")
        return results, summary


