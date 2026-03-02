"""
Output Validators - MVP
Validadores de saída do LLM para prevenir alucinações
"""

from typing import Dict
import logging

# configura logger para este módulo
logger = logging.getLogger(__name__)

#------------------------------------------------------------------------------------------------------------------------------------------------------------------------ 
# classe responsável por validar as saídas do modelo de linguagem
# garantindo que as explicações sejam coerentes, relevantes e não contenham artefatos ou frases genéricas
class OutputValidator:
    """
    Valida saídas do LLM para garantir qualidade
    """
    
    def __init__(self):
        """Inicializa validador com regras de qualidade"""

        # explicações muito curtas geralmente não são úteis ou indicam que o modelo não entendeu o contexto
        # explicações muito longas podem indicar que o modelo está divagando ou incluindo informações irrelevantes
        self.min_explanation_length = 30    # tamanho mínimo de explicações válidas 
        self.max_explanation_length = 600   # tamanho máximo de explicações válidas (ajustável conforme necessidade)

        # frases genéricas ou de desculpas são sinais comuns de que o modelo não tem uma resposta concreta ou está alucinando, então são proibidas
        self.forbidden_phrases = [
            "I don't know",
            "I cannot",
            "As an AI",
            "I'm not sure",
            "[INSERT",
            "TODO",
            "PLACEHOLDER"
        ]

#------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    # método principal para validar explicações geradas pelo LLM, verificando comprimento, presença de frases proibidas e relevância do conteúdo     
    def is_valid_explanation(self, text: str) -> bool:
        """
        Verifica se explicação do LLM é válida
        
        Args:
            text: Texto gerado pelo LLM
        
        Returns:
            True se explicação é válida
        """

        # verifica se o texto é uma string não vazia
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
    
#------------------------------------------------------------------------------------------------------------------------------------------------------------------------     
    # método para sanitizar explicações, removendo artefatos, formatando o texto e garantindo que seja coerente e relevante
    def sanitize_explanation(self, text: str) -> str:
        """
        Remove artefatos e formata explicação
        
        Args:
            text: Texto bruto do LLM
        
        Returns:
            Texto limpo e formatado
        """

        # verifica se o texto é uma string não vazia antes de tentar processar, para evitar erros
        if not text:
            return ""
        
        # remove espaços extras
        text = " ".join(text.split())
        
        # remove quebras de linha múltiplas
        text = text.replace("\n\n", "\n").strip()
        
        # garante ponto final
        if text and text[-1] not in '.!?':
            text += '.'
        
        # retorna texto sanitizado
        return text
    
#------------------------------------------------------------------------------------------------------------------------------------------------------------------------     
    # método para validar métricas extraídas, garantindo que estejam no formato correto e dentro de ranges esperados
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
        
        # Verifica range de illumination - deve ser um float entre 0 e 1
        illumination = metrics.get('illumination')
        if not isinstance(illumination, (int, float)):
            return False
        if not (0.0 <= illumination <= 1.0):
            return False
        
        # Verifica label válido - deve ser uma string com um dos valores esperados (underexposed, adequate, acceptable, overexposed, poor)
        valid_labels = ['underexposed', 'adequate', 'acceptable', 'overexposed', 'poor']
        if metrics.get('illumination_label') not in valid_labels:
            return False
        
        return True
