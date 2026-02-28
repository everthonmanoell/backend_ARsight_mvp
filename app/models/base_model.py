"""
Base Model for AR Diagnostic MVP
Classe abstrata para modelos de diagnóstico (illumination only)
"""

from abc import ABC, abstractmethod
from typing import Dict, List
import logging

from app.core.rule_engine import RuleEngine
from app.core.validators import OutputValidator
from app.utils.templates import ExplanationTemplates
from app.config.config import Config

logger = logging.getLogger(__name__)


class ARDiagnosticModel(ABC):
    """
    Classe base abstrata para modelos de diagnóstico AR
    Arquitetura híbrida: Rule Engine + LLM + Validation
    """
    
    def __init__(self, use_4bit: bool = True):
        """
        Inicializa modelo de diagnóstico
        
        Args:
            use_4bit: Usar quantização 4-bit para economizar memória
        """
        self.use_4bit = use_4bit
        
        # Carrega thresholds do YAML
        config = Config()
        rule_thresholds = config.get_rule_thresholds()
        self.rule_engine = RuleEngine(thresholds=rule_thresholds)
        
        self.validator = OutputValidator()
        self.templates = ExplanationTemplates()
        self.model = None
        self.tokenizer = None
        
        logger.info(f"Initializing {self.__class__.__name__}")
    
    @abstractmethod
    def _load_model(self):
        """Carrega modelo e tokenizer"""
        pass
    
    @abstractmethod
    def _call_model(self, prompt: str) -> str:
        """
        Chama modelo para gerar texto
        
        Args:
            prompt: Prompt formatado
        
        Returns:
            Texto gerado pelo modelo
        """
        pass
    
    @abstractmethod
    def _build_prompt(self, metrics: Dict, status: str, risk_level: str, 
                     triggered_rules: List[str]) -> str:
        """
        Constrói prompt específico do modelo
        
        Args:
            metrics: Métricas extraídas
            status: Status da decisão (pass/fail)
            risk_level: Nível de risco
            triggered_rules: Regras ativadas
        
        Returns:
            Prompt formatado para o modelo
        """
        pass
    
    def diagnose(self, metrics: Dict) -> Dict:
        """
        Realiza diagnóstico completo
        
        Args:
            metrics: Métricas extraídas (illumination only)
        
        Returns:
            Dicionário com diagnóstico completo
        """
        # Valida métricas
        if not self.validator.validate_metrics(metrics):
            raise ValueError("Invalid metrics format")
        
        # 1. Rule Engine: Decisão determinística
        status, risk_level, triggered_rules = self.rule_engine.evaluate(metrics)
        
        # 2. LLM: Gera explicação
        explanation = self._generate_explanation(
            metrics, status, risk_level, triggered_rules
        )
        
        logger.debug(f"Generated explanation: {explanation[:100]}...")
        
        # 3. Validação: Verifica qualidade
        if not self.validator.is_valid_explanation(explanation, metrics):
            logger.warning("LLM explanation failed validation, using template fallback")
            logger.debug(f"Failed explanation was: {explanation}")
            explanation = self.templates.get_template_explanation(
                status, risk_level, triggered_rules, metrics
            )
        
        # Sanitiza explicação
        explanation = self.validator.sanitize_explanation(explanation)
        
        # Monta resultado
        result = {
            'status': status,
            'risk_level': risk_level,
            'explanation': explanation,
            'metrics': {
                'illumination': metrics.get('illumination'),
                'illumination_label': metrics.get('illumination_label'),
                'mean_brightness': metrics.get('mean_luma', 0) / 255.0  # Normaliza para 0-1
            },
            'triggered_rules': triggered_rules,
            'recommendations': self.rule_engine.build_recommendations(triggered_rules, status)
        }
        
        return result
    
    def _generate_explanation(self, metrics: Dict, status: str, 
                            risk_level: str, triggered_rules: List[str]) -> str:
        """
        Gera explicação usando LLM
        
        Args:
            metrics: Métricas da cena
            status: Status da decisão
            risk_level: Nível de risco
            triggered_rules: Regras ativadas
        
        Returns:
            Explicação gerada (ou template se falhar)
        """
        try:
            # Carrega modelo se necessário
            if self.model is None:
                logger.info("Loading model for first inference...")
                self._load_model()
            
            # Constrói prompt
            prompt = self._build_prompt(metrics, status, risk_level, triggered_rules)
            logger.debug(f"Prompt built (first 200 chars): {prompt[:200]}...")
            
            # Gera explicação
            logger.debug("Calling LLM for explanation generation...")
            explanation = self._call_model(prompt)
            logger.debug(f"LLM returned: {explanation}")
            
            return explanation
            
        except Exception as e:
            logger.error(f"Error generating explanation: {e}", exc_info=True)
            # Fallback para template
            return self.templates.get_template_explanation(
                status, risk_level, triggered_rules, metrics
            )
    
    def diagnose_batch(self, metrics_list: List[Dict]) -> List[Dict]:
        """
        Diagnostica múltiplas cenas em batch (mais eficiente que sequencial)
        
        Args:
            metrics_list: Lista de dicionários com métricas
        
        Returns:
            Lista de diagnósticos
        """
        logger.info(f"Batch diagnosis for {len(metrics_list)} scenes...")
        
        # Carrega modelo se necessário
        if self.model is None:
            logger.info("Loading model for first inference...")
            self._load_model()
        
        results = []
        
        # Fase 1: Avaliação determinística (rápido)
        evaluations = []
        for metrics in metrics_list:
            if not self.validator.validate_metrics(metrics):
                raise ValueError("Invalid metrics format in batch")
            
            status, risk_level, triggered_rules = self.rule_engine.evaluate(metrics)
            evaluations.append((metrics, status, risk_level, triggered_rules))
        
        # Fase 2: Geração de explicações (pode ser otimizado)
        # Por enquanto processa sequencialmente, mas com modelo já carregado
        for metrics, status, risk_level, triggered_rules in evaluations:
            explanation = self._generate_explanation(
                metrics, status, risk_level, triggered_rules
            )
            
            if not self.validator.is_valid_explanation(explanation, metrics):
                logger.debug("Explanation failed validation, using template")
                explanation = self.templates.get_template_explanation(
                    status, risk_level, triggered_rules, metrics
                )
            
            explanation = self.validator.sanitize_explanation(explanation)
            
            result = {
                'status': status,
                'risk_level': risk_level,
                'explanation': explanation,
                'metrics': {
                    'illumination': metrics.get('illumination'),
                    'illumination_label': metrics.get('illumination_label'),
                    'mean_brightness': metrics.get('mean_luma', 0) / 255.0
                },
                'triggered_rules': triggered_rules,
                'recommendations': self.rule_engine.build_recommendations(triggered_rules, status)
            }
            
            results.append(result)
        
        logger.info(f"Batch completed: {len(results)} diagnoses generated")
        return results

