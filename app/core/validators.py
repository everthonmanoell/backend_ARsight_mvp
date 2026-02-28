"""
Output Validators - MVP
Validadores de saída do LLM para prevenir alucinações
"""

from typing import Dict
import logging

logger = logging.getLogger(__name__)


class OutputValidator:
    """
    Valida saídas do LLM para garantir qualidade
    """
    
    def __init__(self):
        """Inicializa validador com regras de qualidade"""
        self.min_explanation_length = 30
        self.max_explanation_length = 600
        self.forbidden_phrases = [
            "I don't know",
            "I cannot",
            "As an AI",
            "I'm not sure",
            "[INSERT",
            "TODO",
            "PLACEHOLDER"
        ]
    
    def is_valid_explanation(self, text: str, metrics: Dict) -> bool:
        """
        Verifica se explicação do LLM é válida
        
        Args:
            text: Texto gerado pelo LLM
            metrics: Métricas da cena
        
        Returns:
            True se explicação é válida
        """
        if not text or not isinstance(text, str):
            logger.debug("Validation failed: text is empty or not string")
            return False
        
        # Verifica comprimento
        if len(text) < self.min_explanation_length:
            logger.debug(f"Validation failed: text too short ({len(text)} < {self.min_explanation_length})")
            return False
        
        if len(text) > self.max_explanation_length:
            logger.debug(f"Validation failed: text too long ({len(text)} > {self.max_explanation_length})")
            return False
        
        # Verifica frases proibidas
        text_lower = text.lower()
        for phrase in self.forbidden_phrases:
            if phrase.lower() in text_lower:
                logger.debug(f"Validation failed: forbidden phrase found: '{phrase}'")
                return False
        
        # Verifica se menciona contexto de iluminação
        has_context = any(word in text_lower for word in [
            'illumination', 'lighting', 'exposure', 'underexposed', 
            'overexposed', 'brightness', 'dark', 'bright', 'light',
            'shadows', 'contrast', 'ar', 'tracking', 'scene'
        ])
        
        if not has_context:
            logger.debug("Validation failed: no relevant context words found")
            return False
        
        logger.debug("Validation passed!")
        return True
    
    def sanitize_explanation(self, text: str) -> str:
        """
        Remove artefatos e formata explicação
        
        Args:
            text: Texto bruto do LLM
        
        Returns:
            Texto limpo e formatado
        """
        if not text:
            return ""
        
        # Remove espaços extras
        text = " ".join(text.split())
        
        # Remove quebras de linha múltiplas
        text = text.replace("\n\n", "\n").strip()
        
        # Garante ponto final
        if text and text[-1] not in '.!?':
            text += '.'
        
        return text
    
    def validate_metrics(self, metrics: Dict) -> bool:
        """
        Valida se métricas estão em formato correto
        
        Args:
            metrics: Dicionário de métricas
        
        Returns:
            True se métricas são válidas
        """
        # Verifica presença de chaves obrigatórias
        required_keys = ['illumination', 'illumination_label']
        
        for key in required_keys:
            if key not in metrics:
                return False
        
        # Verifica range de illumination
        illumination = metrics.get('illumination')
        if not isinstance(illumination, (int, float)):
            return False
        if not (0.0 <= illumination <= 1.0):
            return False
        
        # Verifica label válido
        valid_labels = ['underexposed', 'adequate', 'acceptable', 'overexposed', 'poor']
        if metrics.get('illumination_label') not in valid_labels:
            return False
        
        return True
