"""
Base Model for AR Diagnostic MVP
Classe abstrata para modelos de diagnóstico (illumination only)
"""

from abc import ABC, abstractmethod
from typing import Dict, List
import logging
import re
import random
from collections import Counter

from app.core.rule_engine import RuleEngine
from app.core.validators import OutputValidator
from app.utils.templates import ExplanationTemplates
from app.config.config import Config

# configura logger para este módulo
logger = logging.getLogger(__name__)

# classe base abstrata para os modelos de diagnóstico, definindo a arquitetura híbrida com Rule Engine, SLM e validação de saídas 
# contém métodos para diagnóstico individual e em batch (com suporte a summary do ambiente)
class ARDiagnosticModel(ABC):
    """
    Classe base abstrata para modelos de diagnóstico AR
    Arquitetura híbrida: Rule Engine + SLM + Validation
    """
    
    def __init__(self, use_4bit: bool = True):

        # flag para usar quantização 4-bit, que reduz uso de memória e pode acelerar inferência em GPUs compatíveis
        self.use_4bit = use_4bit 

        # Carrega configurações do sistema, como thresholds do rule engine e parâmetros dos modelos
        self.config = Config() 
        
        # Motor de regras para diagnóstico determinístico baseado em métricas extraídas (illumination only)
        self.rule_engine = RuleEngine() 
        
        # Validador de saídas do modelo de linguagem para garantir explicações coerentes e relevantes, sem alucinações ou artefatos
        self.validator = OutputValidator() 

        # Templates de explicação para casos onde o modelo de linguagem falha ou gera explicações inválidas
        # garante que o sistema sempre forneça feedback útil e compreensível para o usuário
        self.templates = ExplanationTemplates() 

        # Modelo de linguagem (carregado sob demanda)
        self.model = None 

        # Tokenizer correspondente ao modelo, necessário para construção de prompts e processamento de texto
        self.tokenizer = None 
        
        # Loga a inicialização do modelo
        logger.info(f"Initializing {self.__class__.__name__}") 

    #------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    # método abstrato para carregar o modelo e tokenizer, deve ser implementado por cada modelo específico
    @abstractmethod
    def _load_model(self):
        pass
    #------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    # método abstrato para chamar o modelo e gerar explicação, deve ser implementado por cada modelo específico
    @abstractmethod
    def _call_model(self, prompt: str, max_new_tokens: int = None) -> str:
        pass
    #------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    # método abstrato para processar múltiplos prompts em batch, deve ser implementado por cada modelo específico
    @abstractmethod
    def _call_model_batch(self, prompts: List[str]) -> List[str]:
        """
        Processa múltiplos prompts em um único forward pass (TRUE BATCH).
        Deve ser implementado pelos modelos específicos.
        Não inclui o prompt de summary — este é processado separadamente via _call_model.

        Args:
            prompts: Lista de prompts individuais por frame

        Returns:
            Lista de respostas geradas
        """
        pass
    #------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    # método para construir o prompt específico do modelo, integrando métricas, status, risco e regras ativadas
    @abstractmethod
    def _build_prompt(self, metrics: Dict, status: str, risk_level: str, triggered_rules: List[str]) -> str: 
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
    #------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    # método para limpar a resposta do modelo, truncando na última frase completa para evitar cortes mid-sentence
    def _clean_response(self, text: str) -> str:
        """Trunca na última frase completa para evitar cortes mid-sentence."""
        # Primário: pontuação final após letra/)/" (evita decimais "0." e marcadores "2.")
        matches = list(re.finditer(r'(?<=[a-zA-Z\)\u201d"])[.!?]', text))
        if matches and matches[-1].end() > 20:
            return text[:matches[-1].end()].strip()
        # Secundário: qualquer pontuação seguida de espaço (provável fim de frase)
        matches2 = list(re.finditer(r'[.!?]\s', text))
        if matches2 and matches2[-1].start() > 20:
            return text[:matches2[-1].start() + 1].strip()
        return text.strip()
    
    #------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    # método para gerar explicação usando o modelo de linguagem, com fallback para template em caso de falha
    def _generate_explanation(self, metrics: Dict, status: str, risk_level: str, triggered_rules: List[str]) -> str:
        """
        Gera explicação usando SLM
        
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
            logger.debug(f"Prompt built: {prompt}")
            
            # Gera explicação
            logger.debug("Calling SLM for explanation generation...")
            explanation = self._call_model(prompt)
            logger.debug(f"SLM returned: {explanation}")
            
            return explanation
            
        except Exception as e:
            logger.error(f"Error generating explanation: {e}", exc_info=True)
            # Fallback para template
            return self.templates.get_template_explanation(status, risk_level, triggered_rules, metrics)
    
    #------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    # método principal para diagnóstico individual, que chama o rule engine, gera explicação e valida a saída
    def diagnose(self, metrics: Dict) -> Dict: 
        """
        Realiza diagnóstico completo
        
        Args:
            metrics: Métricas extraídas (illumination only)
        
        Returns:
            Dicionário com diagnóstico completo
        """
        # Verificar se métricas são válidas antes de prosseguir, garantindo que o rule engine e o modelo de linguagem recebam dados no formato esperado
        if not self.validator.validate_metrics(metrics):
            raise ValueError("Invalid metrics format")
        
        # 1. Rule Engine: Decisão determinística para avaliar a qualidade da cena com base em thresholds pré-definidos
        status, risk_level, triggered_rules = self.rule_engine.evaluate(metrics) 
        
        # 2. SLM: Gera explicação
        explanation = self._generate_explanation(metrics, status, risk_level, triggered_rules)
        
        logger.debug(f"Generated explanation: {explanation}") # Loga explicação gerada para debug
        
        # 3. Validação: Verifica qualidade da explicação gerada, se falhar, usa template de fallback para garantir resposta útil
        if not self.validator.is_valid_explanation(explanation):
            logger.debug(f"Failed explanation was: {explanation}")
            explanation = self.templates.get_template_explanation(status, risk_level, triggered_rules, metrics)
        
        # Sanitiza explicação para remover artefatos, formatar o texto e garantir coerência, mesmo no caso de fallback para template
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
    
    #------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    # método para diagnóstico em batch, processando múltiplas cenas de forma sequencial
    def diagnose_batch(self, metrics_list: List[Dict]) -> List[Dict]: 
        """
        Diagnostica múltiplas cenas em batch (TRUE BATCH INFERENCE):
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

        #----------------------------------------------------------------------------------------------------------------------------------------------------------------------
        # Fase 1: Avaliação determinística usando PDI
        #----------------------------------------------------------------------------------------------------------------------------------------------------------------------

        # lista para armazenar status, risco e regras ativadas de cada cena, que serão usados para construir os prompts em batch
        evaluations = [] 

        # processar cada cena garantindo que as métricas estejam no formato correto antes de passar para o rule engine
        for metrics in metrics_list:
            if not self.validator.validate_metrics(metrics):
                raise ValueError("Invalid metrics format in batch")
            
            status, risk_level, triggered_rules = self.rule_engine.evaluate(metrics) 
            evaluations.append((metrics, status, risk_level, triggered_rules))

        #----------------------------------------------------------------------------------------------------------------------------------------------------------------------
        # Fase 2: Construção de prompts
        #----------------------------------------------------------------------------------------------------------------------------------------------------------------------

        # lista de prompts a ser construída para o batch
        prompts = [] 

        for metrics, status, risk_level, triggered_rules in evaluations:
            prompt = self._build_prompt(metrics, status, risk_level, triggered_rules)
            prompts.append(prompt)

        #----------------------------------------------------------------------------------------------------------------------------------------------------------------------
        # Fase 3: Batch inference (TRUE BATCH - todos os prompts em um forward pass)
        #----------------------------------------------------------------------------------------------------------------------------------------------------------------------
        
        logger.info(f"Generating {len(prompts)} explanations in batch...")

        try:
            # Chama o modelo para processar todos os prompts em um único forward pass, retornando uma lista de explicações geradas
            explanations = self._call_model_batch(prompts) 

        except Exception as e:

            # Loga falha na geração em batch e inicia fallback para processamento sequencial(mais robusto, mas pode ser mais lento)
            # garante que o sistema continue funcionando mesmo em caso de problemas com a geração em batch
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

        #----------------------------------------------------------------------------------------------------------------------------------------------------------------------
        # Fase 4: Validação e montagem de resultados
        #----------------------------------------------------------------------------------------------------------------------------------------------------------------------
        
        # lista para armazenar resultados finais, incluindo status, risco, explicação validada, métricas e recomendações para cada cena
        results = []

        # percorrer cada cena, validando a explicação gerada e usando template de fallback se necessário
        for (metrics, status, risk_level, triggered_rules), explanation in zip(evaluations, explanations):

            if not self.validator.is_valid_explanation(explanation):
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
    
    #------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    # método para construir o prompt de summary do ambiente, integrando estatísticas agregadas das cenas processadas(contagem de problemas, condição dominante e risco geral)
    def _build_summary_prompt(self, agg: Dict) -> str: 
        """
        Constrói prompt de sumarização do ambiente.
        Deve ser sobrescrito por modelos com formato de prompt específico.
        """
        dominant = agg.get('dominant_label', 'unknown')  # condição dominante entre as cenas problemáticas (ex: overexposed, underexposed)
        risk     = agg.get('overall_risk', 'unknown')    # risco geral do ambiente, baseado na pior condição encontrada 
        pcount   = agg.get('problem_count', 0)           # contagem de cenas problemáticas
        total    = agg.get('total', 0)                   # contagem total de cenas processadas
        return (
            f"Environment: {pcount}/{total} frames problematic. "
            f"Dominant condition: {dominant}. Risk: {risk}. "
            f"Avg brightness: {agg.get('avg_mean_luma', 0):.1f}/255. " 
            f"Summarize lighting impact on AR tracking and give recommendations:"
        )
    
    #------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    # método para diagnóstico em batch com geração de summary do ambiente usando um único forward pass (N+1 prompts)
    def diagnose_batch_with_summary(self, metrics_list: List[Dict]): 
        """
        Diagnostica N cenas + gera summary do ambiente num unico batch SLM (N+1 prompts).

        Returns:
            tuple (individual_results: List[Dict], summary: Dict)
        """
    
        logger.info(f"Batch+summary inference for {len(metrics_list)} scenes (N+1 prompts)...")

        # Carrega modelo se necessário
        if self.model is None:
            self._load_model()

        #----------------------------------------------------------------------------------------------------------------------------------------------------------------------
        # Fase 1: Avaliação determinística usando PDI
        #----------------------------------------------------------------------------------------------------------------------------------------------------------------------

        # lista para armazenar status, risco e regras ativadas de cada cena, que serão usados para construir os prompts em batch
        evaluations = [] 

        # processar cada cena garantindo que as métricas estejam no formato correto antes de passar para o rule engine
        for metrics in metrics_list:
            if not self.validator.validate_metrics(metrics):
                raise ValueError("Invalid metrics format in batch")
            
            status, risk_level, triggered_rules = self.rule_engine.evaluate(metrics) 
            evaluations.append((status, risk_level, triggered_rules))

        #----------------------------------------------------------------------------------------------------------------------------------------------------------------------
        # Fase 2: Agregar estatísticas para o prompt de summary
        #----------------------------------------------------------------------------------------------------------------------------------------------------------------------
        
        # lista de labels qualitativos de iluminação para cada cena, usada para determinar a condição dominante e a distribuição de problemas
        labels = [m.get('illumination_label', 'unknown') for m in metrics_list] 

        # lista de níveis de risco para cada cena, usada para determinar o risco geral do ambiente (baseado na pior condição encontrada)
        risk_levels = [e[1] for e in evaluations] 

        # contagem de cenas problemáticas, usada para calcular a proporção de problemas no ambiente e informar o summary
        problem_count = sum(1 for e in evaluations if e[0] == 'fail') 

        # prioridade de risco para determinar o risco geral do ambiente, baseado na pior condição encontrada entre as cenas processadas
        risk_priority = {'high': 3, 'medium': 2, 'low': 1} 

        # risco geral do ambiente, determinado pela pior condição encontrada entre as cenas processadas 
        # (ex: se houver alguma cena com risco 'high', o risco geral será 'high')
        overall_risk = max(risk_levels, key=lambda r: risk_priority.get(r, 0)) 

        # Contagem por categoria de problema (apenas frames com status=fail)
        problem_labels = [m.get('illumination_label', 'unknown') for m, (s, _, __) in zip(metrics_list, evaluations) if s == 'fail']
        label_breakdown = dict(Counter(problem_labels))

        # condição dominante entre as cenas PROBLEMÁTICAS APENAS (não contabiliza frames bons)
        # (ex: se a maioria das cenas problemáticas for 'overexposed', a condição dominante será 'overexposed')
        # se não houver frames com problema, mantém a etiqueta mais frequente geral
        dominant_label = Counter(problem_labels).most_common(1)[0][0] if problem_labels else Counter(labels).most_common(1)[0][0] if labels else 'unknown'
        
        # contagem total de cenas processadas, usada para calcular proporção de problemas e informar o summary
        n = len(metrics_list)

        # estatísticas agregadas para o prompt de summary, integrando contagem total, contagem de problemas, condição dominante e risco geral
        agg = { 
            'total':               n,
            'problem_count':       problem_count,
            'dominant_label':      dominant_label,
            'overall_risk':        overall_risk,
            'label_breakdown':     label_breakdown,  # ex: {'overexposed': 4, 'underexposed': 3}
            'avg_mean_luma':       sum(m.get('mean_luma', 0) for m in metrics_list) / n,
            'avg_uniformity':      sum(m.get('uniformity', 0) for m in metrics_list) / n,
            'avg_pct_clipped_bright': sum(m.get('pct_clipped_bright', 0) for m in metrics_list) / n,
            'avg_pct_clipped_dark':   sum(m.get('pct_clipped_dark', 0) for m in metrics_list) / n,
        }

        #----------------------------------------------------------------------------------------------------------------------------------------------------------------------
        # Fase 3: Construir N prompts individuais + 1 prompt de summary
        #----------------------------------------------------------------------------------------------------------------------------------------------------------------------

        # O summary é adicionado ao batch — mesmo forward pass, sem custo extra de recompilação JIT.
        # O prompt de summary é mais curto mas o padding left garante alinhamento correto (padding_side='left' no tokenizer).

        # prompts individuais para cada cena
        individual_prompts = [self._build_prompt(m, s, r, rules) for m, (s, r, rules) in zip(metrics_list, evaluations)] 

        # prompt específico para sumarização do ambiente
        summary_prompt = self._build_summary_prompt(agg) 

        #----------------------------------------------------------------------------------------------------------------------------------------------------------------------
        # Fase 4: Batch inference para N prompts individuais
        #----------------------------------------------------------------------------------------------------------------------------------------------------------------------
        # Cada explicação individual usa self.max_tokens (curto, ~1-2 frases por frame)
        try:
            individual_responses = self._call_model_batch(individual_prompts)
        except Exception as e:

            logger.warning(f"Batch generation failed: {e}, falling back to sequential")

            individual_responses = []

            for p in individual_prompts:
                try:
                    individual_responses.append(self._call_model(p))
                except Exception as e2:
                    individual_responses.append("")

        #----------------------------------------------------------------------------------------------------------------------------------------------------------------------
        # Fase 5: Inferência separada para o summary (mais tokens — é o texto principal da interface)
        #----------------------------------------------------------------------------------------------------------------------------------------------------------------------
        # summary é gerado em chamada separada com self.summary_max_tokens

        # fallback para garantir que o summary tenha mais tokens se a configuração específica não estiver presente
        summary_max = getattr(self, 'summary_max_tokens', self.max_tokens) 

        try:

            summary_response = self._call_model(summary_prompt, max_new_tokens=summary_max)

        except Exception as e:

            logger.warning(f"Summary generation failed: {e}")

            summary_response = ""

        #----------------------------------------------------------------------------------------------------------------------------------------------------------------------
        # Fase 6: Validação e montagem de resultados finais para cada cena, integrando explicação gerada (ou template de fallback), métricas, status, risco e recomendações
        #----------------------------------------------------------------------------------------------------------------------------------------------------------------------

        # lista para armazenar resultados finais
        results = [] 

        # percorrer cada cena, validando a explicação gerada e usando template de fallback se necessário
        for metrics, (status, risk, rules), explanation in zip(metrics_list, evaluations, individual_responses):
            if not self.validator.is_valid_explanation(explanation):
                explanation = self.templates.get_template_explanation(status, risk, rules, metrics)
            explanation = self.validator.sanitize_explanation(explanation)
            results.append({
                'status':          status,
                'risk_level':      risk,
                'explanation':     explanation,
                'triggered_rules': rules,
                'recommendations': self.rule_engine.build_recommendations(rules, status)
            })

        #----------------------------------------------------------------------------------------------------------------------------------------------------------------------
        # Fase 7: Montar summary do ambiente 
        #----------------------------------------------------------------------------------------------------------------------------------------------------------------------

        # Sanitiza o texto do summary para garantir coerência e legibilidade
        summary_text = self._clean_response(summary_response) if summary_response else ""

        # VALIDAÇÃO: Verifica alucinações e qualidade, mas permite geração natural
        if not self.validator.is_valid_explanation(summary_text):
            logger.debug(f"Summary failed validation, generating fallback")
            # Fallback variado - múltiplas opções determinísticas baseadas em dados
            # Isso evita repetição e mantém consistência com os dados do batch
            
            label_desc = {
                'overexposed': 'excessive brightness',
                'underexposed': 'insufficient lighting',
                'poor': 'uneven illumination',
            }
            dominant_desc = label_desc.get(dominant_label, 'lighting issues')
            total_frames = n
            
            if problem_count > 0:
                modal_verb = 'could' if overall_risk == 'high' else 'may'
                fallback_options = [
                    f"In this batch, {problem_count} of {total_frames} frames show {dominant_desc}, which {modal_verb} affect AR tracking stability.",
                    f"The batch contains {problem_count} problematic frames with {dominant_desc}; AR performance {modal_verb} be reduced.",
                    f"{dominant_desc.capitalize()} appears in {problem_count} of {total_frames} frames, creating risk for reliable AR tracking.",
                    f"Lighting analysis shows {problem_count}/{total_frames} frames with {dominant_desc}, which {modal_verb} impact AR quality.",
                    f"Frame batch review ({total_frames} total): {problem_count} frames detected with {dominant_label} conditions. AR performance {modal_verb} be affected.",
                ]
                summary_text = random.choice(fallback_options)
            else:
                fallback_options = [
                    f"All {total_frames} frames show lighting conditions suitable for stable AR tracking.",
                    f"No lighting issues were detected in this batch of {total_frames} frames; the scene is ready for AR.",
                    f"The batch presents consistent illumination across {total_frames} frames, supporting reliable AR performance.",
                    f"Lighting is adequate throughout the {total_frames}-frame batch, enabling good AR tracking conditions.",
                    f"All {total_frames} frames meet lighting requirements for AR; conditions are favorable for reliable tracking.",
                ]
                summary_text = random.choice(fallback_options)
        
        summary_text = self.validator.sanitize_explanation(summary_text)

        # Recomendações agrupadas por condição de iluminação (underexposed, acceptable, overexposed, etc)
        # Estrutura: [ { "condition": "adequate_acceptable", "frames": [0,1,5,...], "count": 9, "actions": [...] }, ... ]

        # dicionário para agrupar frame indices e ações por illumination_label
        rec_by_condition = {}  

        # iterar sobre cada frame para coletar suas métricas, recomendações e índice
        for idx, (metrics, (status, risk, rules), result) in enumerate(zip(metrics_list, evaluations, results)):
            
            # obtém o label de iluminação (acceptable, adequate, underexposed, overexposed, etc)
            condition = metrics.get('illumination_label', 'unknown')

            # agrupa "adequate" e "acceptable" em um único label para recomendações
            # ambos representam condições OK para AR
            if condition in ['adequate', 'acceptable']:
                condition = 'adequate_acceptable'

            # inicializa a entrada para essa condição se não existir
            if condition not in rec_by_condition:
                rec_by_condition[condition] = {
                    'frames': [],
                    'actions_set': set()
                }

            # adiciona o índice do frame para essa condição
            rec_by_condition[condition]['frames'].append(idx)

            # coleta as ações recomendadas para essa condição (deduplicação com set)
            for rec in self.rule_engine.build_recommendations(rules, status):
                rec_by_condition[condition]['actions_set'].add(rec)

        # converte o dicionário em array ordenado de recomendações por condição
        # ordena por condição para garantir consistência (optimal, overexposed, underexposed)
        condition_order = ['adequate_acceptable', 'overexposed', 'underexposed', 'poor', 'unknown']
        recommendations_by_condition = []

        for condition in condition_order:
            if condition in rec_by_condition:
                data = rec_by_condition[condition]
                recommendations_by_condition.append({
                    'condition': condition,
                    'frames': sorted(data['frames']),
                    'count': len(data['frames']),
                    'actions': sorted(list(data['actions_set']))  # ordena ações para consistência
                })

        summary = {
            'overall_risk':   overall_risk,
            'dominant_label': dominant_label,
            'problem_count':  problem_count,
            'normal_count':   n - problem_count,
            'explanation':    summary_text,
            'recommendations': recommendations_by_condition,
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

