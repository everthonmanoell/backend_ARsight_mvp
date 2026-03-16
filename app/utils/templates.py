"""
Explanation Templates - MVP
Templates de fallback para explicações quando SLM falha
"""

from typing import Dict, List

# classe que fornece templates de explicação para casos em que o modelo SLM falha ou não consegue gerar uma explicação adequada
class ExplanationTemplates:
    """
    Fornece templates sucintos para fallback.
    Uma frase por template, sem redundância.
    """
    
    def __init__(self):
        """Inicializa templates breves"""
        import random
        random.seed()

        # Templates sucesso - PASS (breves)
        self.pass_templates = [
            "Optimal lighting enables stable AR tracking.",
            "Good brightness and uniformity support AR operations.",
            "Strong lighting conditions provide reliable AR tracking.",
            "Adequate illumination ensures consistent AR performance.",
        ]
        
        # Templates falha - breves por tipo
        self.fail_templates = {
            'underexposed': [
                "Low light severely limits feature visibility.",
                "Insufficient brightness degrades AR tracking.",
                "Dark conditions prevent reliable feature detection.",
                "Low light levels harm AR accuracy.",
            ],
            'overexposed': [
                "Excessive brightness washes out visual detail.",
                "Highlight clipping impairs AR feature matching.",
                "Overexposure reduces visual contrast needed for AR.",
                "High brightness eliminates subtle AR markers.",
            ],
            'poor_illumination': [
                "Uneven lighting disrupts AR feature consistency.",
                "Lighting variation harms AR tracking stability.",
                "Poor uniformity compromises AR performance.",
                "Shadowed areas reduce AR feature availability.",
            ]
        }
    
    def get_template_explanation( 
        self,
        status: str,
        risk_level: str,
        triggered_rules: List[str],
        metrics: Dict
    ) -> str:
        """
        Gera explicação baseada em templates com variação

        Args:
            status: 'pass' ou 'fail'
            risk_level: Nível de risco
            triggered_rules: Regras ativadas
            metrics: Métricas da cena

        Returns:
            Explicação formatada
        """
        import random

        if status == 'pass':
            return random.choice(self.pass_templates)
        
        # Status = fail, escolhe template apropriado
        rule_mapping = {
            'Underexposed scene (too dark)': 'underexposed',
            'Overexposed scene (too bright)': 'overexposed',
            'Poor illumination quality': 'poor_illumination'
        }
        
        for rule in triggered_rules:
            if rule in rule_mapping:
                template_key = rule_mapping[rule]
                templates = self.fail_templates[template_key]
                return random.choice(templates)
        
        # Fallback genérico
        return random.choice(self.fail_templates['poor_illumination'])
