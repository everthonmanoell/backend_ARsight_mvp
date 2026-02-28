"""
Explanation Templates - MVP
Templates de fallback para explicações quando LLM falha
"""

from typing import Dict, List


class ExplanationTemplates:
    """
    Fornece templates de explicação para fallback
    """
    
    def __init__(self):
        """Inicializa templates"""
        self.pass_templates = {
            'low': (
                "The scene presents optimal illumination conditions for AR deployment with "
                "adequate lighting levels, ensuring stable tracking and reliable anchor placement."
            )
        }
        
        self.fail_templates = {
            'underexposed': (
                "The scene is severely underexposed with insufficient lighting, resulting in poor feature visibility "
                "and compromised AR tracking accuracy."
            ),
            'overexposed': (
                "The scene is severely overexposed with excessive brightness, causing loss of visual detail "
                "and degraded AR tracking performance."
            ),
            'poor_illumination': (
                "Inadequate illumination conditions compromise visual quality and feature detection, "
                "negatively impacting AR tracking accuracy and anchor placement reliability."
            )
        }
    
    def get_template_explanation(
        self,
        status: str,
        risk_level: str,
        triggered_rules: List[str],
        metrics: Dict
    ) -> str:
        """
        Gera explicação baseada em templates
        
        Args:
            status: 'pass' ou 'fail'
            risk_level: Nível de risco
            triggered_rules: Regras ativadas
            metrics: Métricas da cena
        
        Returns:
            Explicação formatada
        """
        if status == 'pass':
            return self.pass_templates['low']
        
        # Status = fail, escolhe template apropriado
        rule_mapping = {
            'Underexposed scene (too dark)': 'underexposed',
            'Overexposed scene (too bright)': 'overexposed',
            'Poor illumination quality': 'poor_illumination'
        }
        
        for rule in triggered_rules:
            if rule in rule_mapping:
                template_key = rule_mapping[rule]
                return self.fail_templates[template_key]
        
        # Fallback genérico
        return self.fail_templates['poor_illumination']
