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
        Diagnostica múltiplas cenas em batch (TRUE BATCH INFERENCE)
        Processa múltiplos prompts em um único forward pass
        
        Args:
            metrics_list: Lista de dicionários com métricas
        
        Returns:
            Lista de diagnósticos
        """
        logger.info(f"True batch inference for {len(metrics_list)} scenes...")
        
        # Carrega modelo se necessário
        if self.model is None:
            logger.info("Loading model for first inference...")
            self._load_model()
        
        # Fase 1: Avaliação determinística (rápido)
        evaluations = []
        for metrics in metrics_list:
            if not self.validator.validate_metrics(metrics):
                raise ValueError("Invalid metrics format in batch")
            
            status, risk_level, triggered_rules = self.rule_engine.evaluate(metrics)
            evaluations.append((metrics, status, risk_level, triggered_rules))
        
        # Fase 2: Construção de prompts
        prompts = []
        for metrics, status, risk_level, triggered_rules in evaluations:
            prompt = self._build_prompt(metrics, status, risk_level, triggered_rules)
            prompts.append(prompt)
        
        # Fase 3: Batch inference (TRUE BATCH - todos os prompts em um forward pass)
        logger.info(f"Generating {len(prompts)} explanations in batch...")
        try:
            explanations = self._call_model_batch(prompts)
        except Exception as e:
            logger.warning(f"Batch generation failed: {e}, falling back to sequential")
            # Fallback para processamento sequencial
            explanations = []
            for prompt in prompts:
                try:
                    expl = self._call_model(prompt)
                    explanations.append(expl)
                except Exception as e2:
                    logger.error(f"Sequential generation also failed: {e2}")
                    explanations.append("")
        
        # Fase 4: Validação e montagem de resultados
        results = []
        for (metrics, status, risk_level, triggered_rules), explanation in zip(evaluations, explanations):
            
            if not self.validator.is_valid_explanation(explanation, metrics):
                logger.debug(f"Explanation failed validation, using template")
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
    
    def _call_model_batch(self, prompts: List[str]) -> List[str]:
        """
        Processa múltiplos prompts em um único forward pass (TRUE BATCH)
        Deve ser implementado pelos modelos específicos
        
        Args:
            prompts: Lista de prompts
        
        Returns:
            Lista de explicações geradas
        """
        # Fallback padrão: processa sequencialmente
        logger.warning("Model doesn't implement _call_model_batch, using sequential processing")
        return [self._call_model(prompt) for prompt in prompts]

    def _build_summary_prompt(self, agg: Dict) -> str:
        """
        Constrói prompt de sumarização do ambiente.
        Deve ser sobrescrito por modelos com formato de prompt específico.
        """
        dominant = agg.get('dominant_label', 'unknown')
        risk     = agg.get('overall_risk', 'unknown')
        pcount   = agg.get('problem_count', 0)
        total    = agg.get('total', 0)
        return (
            f"Environment: {pcount}/{total} frames problematic. "
            f"Dominant condition: {dominant}. Risk: {risk}. "
            f"Avg brightness: {agg.get('avg_mean_luma', 0):.1f}/255. "
            f"Summarize lighting impact on AR tracking and give recommendations:"
        )

    def diagnose_batch_with_summary(self, metrics_list: List[Dict]):
        """
        Diagnostica N cenas + gera summary do ambiente num unico batch LLM (N+1 prompts).

        Returns:
            tuple (individual_results: List[Dict], summary: Dict)
        """
        from collections import Counter

        logger.info(f"Batch+summary inference for {len(metrics_list)} scenes (N+1 prompts)...")

        # Carrega modelo se necessário
        if self.model is None:
            self._load_model()

        # 1. Avaliação determinística
        evaluations = []
        for metrics in metrics_list:
            if not self.validator.validate_metrics(metrics):
                raise ValueError("Invalid metrics format in batch")
            status, risk, rules = self.rule_engine.evaluate(metrics)
            evaluations.append((status, risk, rules))

        # 2. Agrega estatísticas para o prompt de summary
        labels       = [m.get('illumination_label', 'unknown') for m in metrics_list]
        risk_levels  = [e[1] for e in evaluations]
        problem_count = sum(1 for e in evaluations if e[0] == 'fail')
        risk_priority = {'high': 3, 'medium': 2, 'low': 1}
        overall_risk  = max(risk_levels, key=lambda r: risk_priority.get(r, 0))
        dominant_label = Counter(labels).most_common(1)[0][0]
        n = len(metrics_list)

        agg = {
            'total':               n,
            'problem_count':       problem_count,
            'dominant_label':      dominant_label,
            'overall_risk':        overall_risk,
            'avg_mean_luma':       sum(m.get('mean_luma', 0) for m in metrics_list) / n,
            'avg_uniformity':      sum(m.get('uniformity', 0) for m in metrics_list) / n,
            'avg_pct_clipped_bright': sum(m.get('pct_clipped_bright', 0) for m in metrics_list) / n,
            'avg_pct_clipped_dark':   sum(m.get('pct_clipped_dark', 0) for m in metrics_list) / n,
        }

        # 3. Constrói N prompts individuais + 1 summary prompt
        prompts = [
            self._build_prompt(m, s, r, rules)
            for m, (s, r, rules) in zip(metrics_list, evaluations)
        ]
        prompts.append(self._build_summary_prompt(agg))

        # 4. Único batch LLM (N+1 forward passes em paralelo)
        try:
            all_responses = self._call_model_batch(prompts)
        except Exception as e:
            logger.warning(f"Batch generation failed: {e}, falling back to sequential")
            all_responses = []
            for p in prompts:
                try:
                    all_responses.append(self._call_model(p))
                except Exception as e2:
                    all_responses.append("")

        individual_responses = all_responses[:-1]
        summary_response     = all_responses[-1]

        # 5. Monta resultados individuais
        results = []
        for metrics, (status, risk, rules), explanation in zip(metrics_list, evaluations, individual_responses):
            if not self.validator.is_valid_explanation(explanation, metrics):
                explanation = self.templates.get_template_explanation(status, risk, rules, metrics)
            explanation = self.validator.sanitize_explanation(explanation)
            results.append({
                'status':          status,
                'risk_level':      risk,
                'explanation':     explanation,
                'triggered_rules': rules,
                'recommendations': self.rule_engine.build_recommendations(rules, status)
            })

        # 6. Monta summary
        summary_text = self.validator.sanitize_explanation(summary_response)
        # Recomendações deduplicadas de todos os frames problemáticos
        seen_recs = set()
        all_recs  = []
        for status, risk, rules in evaluations:
            for rec in self.rule_engine.build_recommendations(rules, status):
                if rec not in seen_recs:
                    seen_recs.add(rec)
                    all_recs.append(rec)

        summary = {
            'overall_risk':   overall_risk,
            'dominant_label': dominant_label,
            'problem_count':  problem_count,
            'normal_count':   n - problem_count,
            'explanation':    summary_text,
            'recommendations': all_recs,
            'metrics_avg': {
                'mean_brightness':   round(agg['avg_mean_luma'] / 255.0, 4),
                'mean_luma':         round(agg['avg_mean_luma'], 2),
                'uniformity':        round(agg['avg_uniformity'], 4),
                'pct_clipped_bright': round(agg['avg_pct_clipped_bright'], 4),
                'pct_clipped_dark':   round(agg['avg_pct_clipped_dark'], 4),
            }
        }

        logger.info(f"Batch+summary completed: {len(results)} diagnoses + 1 summary")
        return results, summary

