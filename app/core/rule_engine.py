"""
Rule Engine - MVP Illumination Only
Lógica determinística para decisão PASS/FAIL baseada em iluminação
uso: implementado como parte do modelo base, usado para avaliar métricas extraídas e gerar diagnóstico e recomendações
- Avalia métricas de iluminação (luminância média, uniformidade, clipping) e classifica a condição de iluminação (underexposed, adequate, acceptable, overexposed, poor)
- Gera diagnóstico PASS/FAIL e nível de risco (low, medium, high) baseado na classificação de iluminação
- Fornece evidências formatadas para o modelo de linguagem e recomendações específicas para cada condição de iluminação
"""

import logging
from typing import Dict, List, Tuple

# configura logger para este módulo
logger = logging.getLogger(__name__)

#------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# classe principal do rule engine, responsável por avaliar as métricas extraídas e tomar decisões de diagnóstico AR
class RuleEngine:
    """
    Rule-based decision engine para diagnóstico AR (illumination only)
    """
    
    def __init__(self):
        logger.debug("RuleEngine initialized")

#------------------------------------------------------------------------------------------------------------------------------------------------------------------------    
    # método que avalia as métricas extraídas e retorna decisão, nível de risco e regras ativadas
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

        # Lista de regras que falharam, usada para explicar o diagnóstico e dar recomendações específicas
        triggered_rules = [] 
        
        # Extrai label de iluminação do analisador PDI, que já integra várias features (luminância média, uniformidade, clipping) em uma classificação qualitativa
        illumination_label = metrics.get('illumination_label', 'unknown')
        
        # Regras de iluminação baseadas apenas no label do analisador
        if illumination_label == 'underexposed':
            triggered_rules.append("Underexposed scene (too dark)")
        elif illumination_label == 'overexposed':
            triggered_rules.append("Overexposed scene (too bright)")
        elif illumination_label == 'poor':
            triggered_rules.append("Poor illumination quality")
        # os labels 'adequate' e 'acceptable' são PASS
        

        # Decisão final

        # verificar se alguma regra falhou, se não, é PASS com risco baixo(low risk)
        if len(triggered_rules) == 0:
            status = 'pass'
            risk_level = 'low'

        # se falhou, status é FAIL
        else:
            status = 'fail'
            # Risco alto se underexposed/overexposed, médio se poor
            if 'Underexposed' in triggered_rules[0] or 'Overexposed' in triggered_rules[0]:
                risk_level = 'high'
            else:
                risk_level = 'medium'
        
        # loga detalhes da avaliação para debug
        logger.debug(f"Evaluation: status={status}, risk={risk_level}, rules={triggered_rules}") 
        
        # retorna status, nível de risco e regras ativadas para uso na explicação e recomendações
        return status, risk_level, triggered_rules

#------------------------------------------------------------------------------------------------------------------------------------------------------------------------    
    # método para formatar métricas como evidências para o modelo de linguagem
    # pode ser expandido para incluir mais detalhes ou formatação específica
    def get_evidence_metrics(self, metrics: Dict) -> Dict:
        """
        Retorna métricas formatadas como evidências
        
        Args:
            metrics: Métricas extraídas
        
        Returns:
            Dicionário com evidências formatadas
        """
        # Score de qualidade de iluminação (0-1)
        illumination = metrics.get('illumination', 0.0)  

        # Label qualitativo de iluminação, já considerando clipping e luminância média                  
        illumination_label = metrics.get('illumination_label', 'unknown')
        
        return {
            'illumination': f"{illumination_label} ({illumination:.2f})"
        }
    
#------------------------------------------------------------------------------------------------------------------------------------------------------------------------    
    # método para construir recomendações baseadas nas regras ativadas ou status geral
    # pode ser expandido para incluir recomendações mais específicas ou detalhadas
    def build_recommendations(self, triggered_rules: List[str], status: str = 'fail') -> List[str]:
        """
        Constrói recomendações baseadas nas regras ativadas ou status
        
        Args:
            triggered_rules: Lista de regras que falharam
            status: 'pass' ou 'fail'
        
        Returns:
            Lista de recomendações
        """

        # lista de recomendações a ser construída
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
