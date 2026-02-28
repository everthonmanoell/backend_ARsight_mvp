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
        
        # Extrai label de iluminação do analisador PDI
        # O IlluminationAnalyzer já faz a classificação completa considerando
        # clipping, luminância média e score - confiamos nessa classificação
        illumination_label = metrics.get('illumination_label', 'unknown')
        
        # Regras de iluminação baseadas apenas no label do analisador
        if illumination_label == 'underexposed':
            triggered_rules.append("Underexposed scene (too dark)")
        elif illumination_label == 'overexposed':
            triggered_rules.append("Overexposed scene (too bright)")
        elif illumination_label == 'poor':
            triggered_rules.append("Poor illumination quality")
        # 'adequate' e 'acceptable' são PASS
        
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
    
    def build_recommendations(self, triggered_rules: List[str], status: str = 'fail') -> List[str]:
        """
        Constrói recomendações baseadas nas regras ativadas ou status
        
        Args:
            triggered_rules: Lista de regras que falharam
            status: 'pass' ou 'fail'
        
        Returns:
            Lista de recomendações
        """
        recommendations = []
        
        # Se PASS, dá recomendações positivas para manter condições
        if status == 'pass' and len(triggered_rules) == 0:
            recommendations.append("Current lighting conditions are ideal for AR. Maintain these settings for optimal performance")
            recommendations.append("Ensure consistent lighting throughout the AR session to preserve quality")
            return recommendations
        
        # Se FAIL, dá recomendações corretivas
        for rule in triggered_rules:
            if 'Underexposed' in rule or 'too dark' in rule:
                recommendations.append("Increase ambient lighting or use supplemental light sources")
                recommendations.append("Position light sources to evenly illuminate the scene")
            elif 'Overexposed' in rule or 'too bright' in rule:
                recommendations.append("Reduce direct lighting or use diffusers to soften harsh light")
                recommendations.append("Avoid pointing camera directly at bright light sources")
            elif 'Poor illumination' in rule:
                recommendations.append("Improve overall lighting uniformity and reduce shadows")
        
        return recommendations
