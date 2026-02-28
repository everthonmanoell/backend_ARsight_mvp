"""
Rule Engine - MVP Illumination Only
Lógica determinística para decisão PASS/FAIL baseada em iluminação
"""

import logging
from typing import Dict, List, Tuple

logger = logging.getLogger(__name__)


class RuleEngine:
    """
    Rule-based decision engine para diagnóstico AR (illumination only)
    """
    
    def __init__(self, thresholds: Dict = None):
        """
        Inicializa rule engine com thresholds configuráveis
        
        Args:
            thresholds: Dicionário com thresholds do YAML
        """
        self.thresholds = thresholds or {}
        logger.debug(f"RuleEngine initialized with thresholds: {self.thresholds}")
    
    def evaluate(self, metrics: Dict) -> Tuple[str, str, List[str]]:
        """
        Avalia métricas e retorna decisão
        
        Args:
            metrics: Métricas extraídas (illumination only)
        
        Returns:
            tuple: (status, risk_level, triggered_rules)
                - status: 'pass' ou 'fail'
                - risk_level: 'low',  'medium', 'high'
                - triggered_rules: Lista de regras que falharam
        """
        triggered_rules = []
        
        # Extrai threshold de iluminação do YAML
        illum_thresholds = self.thresholds.get('illumination', {})
        underexposed_thr = illum_thresholds.get('underexposed_threshold', 0.35)
        overexposed_thr = illum_thresholds.get('overexposed_threshold', 0.75)
        
        # Verifica iluminação
        illumination = metrics.get('illumination', 0.5)
        illumination_label = metrics.get('illumination_label', 'unknown')
        
        # Regras de iluminação
        if illumination_label == 'underexposed' or illumination < underexposed_thr:
            triggered_rules.append("Underexposed scene (too dark)")
        elif illumination_label == 'overexposed' or illumination > overexposed_thr:
            triggered_rules.append("Overexposed scene (too bright)")
        elif illumination_label == 'poor':
            triggered_rules.append("Poor illumination quality")
        
        # Decisão final
        if len(triggered_rules) == 0:
            status = 'pass'
            risk_level = 'low'
        else:
            status = 'fail'
            # Risco alto se underexposed/overexposed, médio se poor
            if 'Underexposed' in triggered_rules[0] or 'Overexposed' in triggered_rules[0]:
                risk_level = 'high'
            else:
                risk_level = 'medium'
        
        logger.debug(f"Evaluation: status={status}, risk={risk_level}, rules={triggered_rules}")
        
        return status, risk_level, triggered_rules
    
    def get_evidence_metrics(self, metrics: Dict) -> Dict:
        """
        Retorna métricas formatadas como evidências
        
        Args:
            metrics: Métricas extraídas
        
        Returns:
            Dicionário com evidências formatadas
        """
        illumination = metrics.get('illumination', 0.0)
        illumination_label = metrics.get('illumination_label', 'unknown')
        
        return {
            'illumination': f"{illumination_label} ({illumination:.2f})"
        }
    
    def build_recommendations(self, triggered_rules: List[str]) -> List[str]:
        """
        Constrói recomendações baseadas nas regras ativadas
        
        Args:
            triggered_rules: Lista de regras que falharam
        
        Returns:
            Lista de recomendações
        """
        recommendations = []
        
        for rule in triggered_rules:
            if 'Underexposed' in rule or 'too dark' in rule:
                recommendations.append("Increase ambient lighting or use supplemental light sources")
            elif 'Overexposed' in rule or 'too bright' in rule:
                recommendations.append("Reduce direct lighting or use diffusers to soften harsh light")
            elif 'Poor illumination' in rule:
                recommendations.append("Improve overall lighting uniformity and reduce shadows")
        
        return recommendations
