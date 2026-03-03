"""
Phi-3 Mini Model Implementation - MVP Illumination Only
Modelo alternativo com maior qualidade
"""

import logging
from time import time
from typing import Dict, List
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

from app.models.base_model import ARDiagnosticModel
from app.config.config import Config

logger = logging.getLogger(__name__)

# # classe específica para o modelo Phi-3 Mini 3.8B, com otimizações para baixa latência e uso eficiente de VRAM, ideal para Jetson Nano/Xavier NX
class PhiARModel(ARDiagnosticModel):
    """
    Implementação com Phi-3 Mini 3.8B
    
    Características:
    - 3.8B parâmetros (maior qualidade)
    - ~2.5GB VRAM com quantização 4-bit
    - Alternativa ao Qwen para maior qualidade
    """
    
    MODEL_NAME = "microsoft/Phi-3-mini-4k-instruct"
    
    def __init__(self, use_4bit: bool = True, device: str = None):
        """
        Inicializa modelo Phi-3
        
        Args:
            use_4bit: Usar quantização 4-bit
            device: 'cuda', 'cpu', ou 'auto'
        """
        super().__init__(use_4bit)
        
        # Detecta dispositivo
        if device is None or device == 'auto':
            self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        else:
            self.device = device
        
        logger.info(f"Using device: {self.device}")
        
        # Carrega configurações de geração do YAML
        config = Config()
        self.max_tokens = config.get('models.phi.max_tokens', 120)
        self.summary_max_tokens = config.get('models.phi.summary_tokens', 200)

        # Temperatura mais baixa para respostas mais focadas e consistentes, ideal para explicações técnicas
        # A temperatura num modelo de linguagem controla a aleatoriedade da geração: valores mais baixos resultam em respostas mais determinísticas e focadas, 
        # enquanto valores mais altos geram respostas mais variadas e criativas. 
        self.temperature = config.get('models.phi.temperature', 0.4)

        # Top-p sampling (nucleus sampling) é uma técnica de geração onde o modelo considera apenas os tokens mais prováveis que juntos somam uma probabilidade p (ex: 0.9)
        # para manter uma geração focada com alguma diversidade foi usado 0.85
        self.top_p = config.get('models.phi.top_p', 0.85)
        
        logger.info(f"Generation params: max_tokens={self.max_tokens}, summary_max_tokens={self.summary_max_tokens}, temp={self.temperature}, top_p={self.top_p}")
        
        # Carrega modelo
        self._load_model()
    
    #-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    # método para carregar o modelo com as otimizações configuradas 
    def _load_model(self):
        """Carrega Phi-3 Mini"""

        logger.info(f"Loading {self.MODEL_NAME}...")
        
        try:
            # Configuração de quantização 4-bit
            if self.use_4bit and self.device == 'cuda':
                quantization_config = BitsAndBytesConfig(
                    load_in_4bit=True,
                    bnb_4bit_compute_dtype=torch.float16,
                    bnb_4bit_quant_type="nf4",
                    bnb_4bit_use_double_quant=True,
                )
                
                self.model = AutoModelForCausalLM.from_pretrained(
                    self.MODEL_NAME,
                    quantization_config=quantization_config,
                    device_map="auto",
                    dtype=torch.float16,
                    attn_implementation="eager" # otimização para modelos menores, reduz latência em GPUs com menos VRAM
                )
            else:
                # CPU ou sem quantização
                self.model = AutoModelForCausalLM.from_pretrained(
                    self.MODEL_NAME,
                    device_map="auto",
                    dtype=torch.float32 if self.device == 'cpu' else torch.float16,
                    attn_implementation="eager"
                )

                logger.info(f"Model loaded on {self.device}")
            
            # Carrega tokenizer(responsável por converter texto em tokens numéricos que o modelo pode processar)
            # O parâmetro padding_side='left' é crucial para modelos decoder-only, garantindo que o padding seja adicionado à esquerda dos prompts,
            # alinhando corretamente os tokens de entrada e permitindo uma geração mais eficiente e coerente, especialmente em batch.
            self.tokenizer = AutoTokenizer.from_pretrained(
                self.MODEL_NAME,
                padding_side='left'  # Requerido para decoder-only em batch
            )
            
            # Configura pad token(necessário para batch processing, garantindo que os prompts sejam alinhados corretamente)
            # Se o modelo não tiver um pad_token definido, usamos o eos_token como fallback(prática comum para modelos que não possuem um token de padding específico)
            if self.tokenizer.pad_token is None:
                self.tokenizer.pad_token = self.tokenizer.eos_token
            
            # Phi-3 termina respostas com <|end|> — incluir como EOS token
            end_token_id = self.tokenizer.convert_tokens_to_ids("<|end|>")
            eos_id = self.tokenizer.eos_token_id
            self.eos_token_ids = list({eos_id, end_token_id}) if end_token_id != eos_id else [eos_id]
            
            logger.info("Phi-3 Mini loaded successfully")
            
        except Exception as e:
            logger.error(f"Error loading model: {e}")
            raise
    #-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    # método para construir o prompt de diagnóstico para o modelo, formatado para Phi-3, incluindo mensagens do sistema e do usuário, e evidências extraídas das métricas de iluminação
    def _build_prompt(self, metrics: Dict, status: str, risk_level: str, triggered_rules: List[str]) -> str:
        """Constrói prompt para Phi-3"""
        
        # System prompt - específico sobre iluminação (versão MVP focada, pode ser expandida com mais detalhes técnicos ou instruções específicas para o modelo)

        # system_msg define o papel do modelo como um especialista em iluminação para AR, orientando-o a analisar as condições de iluminação 
        system_msg = (
            "You are an AR lighting specialist. Analyze the illumination conditions and explain "
            "how they affect AR tracking and user experience. "
            "Be factual and concise. Write exactly 1-2 sentences, under 50 words total. "
            "Do not use bullet points or lists."
        )
        
        # Extrai evidências
        illumination_label = metrics.get('illumination_label', 'unknown')  # label qualitativo (underexposed, adequate, acceptable, overexposed, poor)
        illumination_score = metrics.get('illumination', 0.0)              # score numérico (0-1)
        mean_luma = metrics.get('mean_luma', 0.0)                          # brilho médio (0-255)
        uniformity = metrics.get('uniformity', 0.0)                        # uniformidade (0-1)
        
        # User prompt define o conteúdo específico para o modelo, incluindo as métricas de iluminação e o status geral
        # solicita uma explicação sobre como essas condições de iluminação impactam a experiência AR, mantendo a resposta técnica e concisa
        if status == 'pass':
            user_msg = (
                f"Lighting Analysis:\n"
                f"- Quality: {illumination_label.upper()}\n"
                f"- Illumination Score: {illumination_score:.2f}\n"
                f"- Mean Brightness: {mean_luma:.1f}/255\n"
                f"- Uniformity: {uniformity:.2f}\n"
                f"- Risk Level: {risk_level.upper()}\n"
                f"Status: PASS\n\n"
                f"Explain why these lighting conditions are optimal for AR applications:"
            )

        # status 'fail' inclui as regras que falharam para fornecer contexto adicional ao modelo sobre os problemas específicos detectados
        else:
            rules_text = '; '.join(triggered_rules)
            user_msg = (
                f"Lighting Analysis:\n"
                f"- Quality: {illumination_label.upper()}\n"
                f"- Illumination Score: {illumination_score:.2f}\n"
                f"- Mean Brightness: {mean_luma:.1f}/255\n"
                f"- Uniformity: {uniformity:.2f}\n"
                f"- Risk Level: {risk_level.upper()}\n"
                f"Status: FAIL\n"
                f"Problems Detected: {rules_text}\n\n"
                f"Explain how these lighting issues specifically impact AR tracking accuracy and visual quality:"
            )
        
        # Phi-3 usa formato específico: <|system|> para mensagens do sistema, <|user|> para mensagens do usuário, e <|assistant|> para a resposta do modelo
        prompt = f"<|system|>\n{system_msg}<|end|>\n<|user|>\n{user_msg}<|end|>\n<|assistant|>\n"
        
        return prompt
    
    #-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    # método para construir o prompt de sumarização do ambiente, agregando as métricas e avaliações de múltiplos frames para fornecer um contexto mais amplo ao modelo 
    # sobre a qualidade geral do ambiente AR, permitindo que ele gere um resumo mais informativo e útil para o usuário final
    def _build_summary_prompt(self, agg: Dict) -> str:
        """Constrói prompt de sumarização do ambiente (formato Phi-3)"""

        total          = agg['total']                     # número total de frames analisados
        problem_count  = agg['problem_count']             # número de frames com problemas de iluminação
        dominant_label = agg['dominant_label']            # label dominante entre os frames problemáticos
        overall_risk   = agg['overall_risk']              # risco geral do ambiente baseado na análise de todos os frames
        avg_luma       = agg['avg_mean_luma']             # brilho médio agregado de todos os frames, fornecendo uma visão geral da luminosidade do ambiente
        avg_uniformity = agg['avg_uniformity']            # uniformidade média agregada, indicando o quão uniforme é a iluminação no ambiente
        avg_clip_bright = agg['avg_pct_clipped_bright']   # porcentagem média de pixels superexpostos, indicando a extensão do problema de brilho excessivo no ambiente
        avg_clip_dark   = agg['avg_pct_clipped_dark']     # porcentagem média de pixels subexpostos, indicando a extensão do problema de escuridão excessiva no ambiente

        system_msg = (
            "You are an AR lighting specialist. Write in plain, natural sentences. "
            "Do not use bullet points, lists, or markdown formatting. "
            "Do not repeat the input data — interpret it and explain what it means for AR use. "
            "Keep your response to 1-2 sentences, under 40 words total."
        )

        # Formata o texto do user prompt para fornecer um resumo claro e conciso da qualidade geral do ambiente de iluminação, 
        # destacando os principais problemas detectados, as métricas agregadas e o risco geral, e solicitando uma explicação 
        # sobre o impacto dessas condições na experiência AR, mantendo a resposta técnica e acessível para o usuário final
        label_names = {
            'overexposed':  'excessively bright',
            'underexposed': 'too dark',
            'poor':         'uneven illumination',
        }
        label_breakdown = agg.get('label_breakdown', {})
        breakdown_parts = [
            f"{count} {label_names.get(lbl, lbl)}"
            for lbl, count in sorted(label_breakdown.items(), key=lambda x: -x[1])
        ]
        breakdown_text = ' and '.join(breakdown_parts) if breakdown_parts else 'problematic'

        user_msg = (
            f"An AR session was evaluated across {total} camera frames. "
            f"{problem_count} frames had lighting problems ({breakdown_text}). "
            f"Dominant issue: {label_names.get(dominant_label, dominant_label)}. "
            f"Average brightness: {avg_luma:.0f}/255, uniformity: {avg_uniformity:.0%}, "
            f"overexposed pixels: {avg_clip_bright:.0%}, underexposed pixels: {avg_clip_dark:.0%}. "
            f"Overall risk: {overall_risk}. "
            f"In 1-2 short sentences, explain what this means for AR and what the user should do:"
        )

        # Formato Phi-3
        prompt = f"<|system|>\n{system_msg}<|end|>\n<|user|>\n{user_msg}<|end|>\n<|assistant|>\n"

        return prompt
    #-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    # método para chamar o modelo com o prompt construído
    def _call_model(self, prompt: str, max_new_tokens: int = None) -> str:
        """Gera explicação com Phi-3 (otimizado)"""

        t0 = time.time() # marca o início da tokenização para medir o tempo gasto nessa etapa

        # tokeniza o prompt, convertendo o texto em uma sequência de tokens numéricos que o modelo pode entender
        inputs = self.tokenizer(  
            prompt,              # texto do prompt a ser tokenizado
            return_tensors="pt", # retorna tensores PyTorch para compatibilidade com o modelo
            truncation=True,     # limita o prompt a um comprimento máximo para evitar erros de entrada muito longa
            max_length=512       # comprimento máximo do prompt
        )
        
        # Move para device do modelo - CPU ou GPU
        device = next(self.model.parameters()).device         # obtém o dispositivo onde o modelo está carregado
        inputs = {k: v.to(device) for k, v in inputs.items()} # move os tensores de entrada 

        t1 = time.time() # marca o fim da tokenização para calcular o tempo gasto nessa etapa

        logger.debug(f"Tokenização: {(t1-t0)*1000:.1f}ms")
        
        # Gera com parâmetros otimizados
        # torch.inference_mode() é mais rápido que torch.no_grad() pois é uma otimização específica para geração
        with torch.no_grad():

            t2 = time.time() # marca o início da geração para medir o tempo gasto nessa etapa

            # gera a resposta do modelo com base nos inputs tokenizados
            outputs = self.model.generate( 
                **inputs,                                                                               # passa os tensores de entrada para o modelo
                max_new_tokens=max_new_tokens if max_new_tokens is not None else self.max_tokens,       # define o número máximo de tokens a serem gerados
                temperature=self.temperature,                                                           # controla a aleatoriedade da geração
                top_p=self.top_p,                                                                       # controla a diversidade da geração usando nucleus sampling
                do_sample=True if self.temperature > 0 else False,                                      # ativa a amostragem se a temperatura for maior que 0
                pad_token_id=self.tokenizer.pad_token_id,                                               # define o token de padding 
                eos_token_id=self.tokenizer.eos_token_id                                                # define o token de end-of-sequence para indicar quando a geração deve parar
            )

            t3 = time.time() # marca o fim da geração para calcular o tempo gasto nessa etapa

            # calcula o número de tokens gerados subtraindo o comprimento dos tokens de entrada do comprimento total dos tokens de saída
            num_tokens = outputs[0].shape[0] - inputs['input_ids'].shape[1] 

            logger.info(f"Geração SLM(Phi): {(t3-t2):.2f}s ({num_tokens} tokens)")
            
        # Decodifica APENAS os tokens novos (otimização crítica)
        t4 = time.time() # marca o início da decodificação para medir o tempo gasto nessa etapa

        input_length = inputs['input_ids'].shape[1]  # comprimento dos tokens de entrada para identificar onde começa a resposta gerada
        generated_tokens = outputs[0][input_length:] # extrai apenas os tokens gerados, ignorando os tokens de entrada para evitar confusão na resposta final

        # decodifica os tokens gerados de volta para texto, removendo tokens especiais e espaços extras
        response = self.tokenizer.decode(generated_tokens, skip_special_tokens=True).strip() 

        t5 = time.time() # marca o fim da decodificação para calcular o tempo gasto nessa etapa

        logger.debug(f"Decodificação: {(t5-t4)*1000:.1f}ms")

        # Fallback se extração falhar
        if not response or len(response) < 10:
            # decodifica toda a saída como fallback para garantir que tenhamos algum texto para processar, mesmo que a extração dos tokens gerados falhe
            full_output = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            # usa o marcador <|assistant|> (formato Phi-3) para localizar o início da resposta gerada
            if "<|assistant|>" in full_output:
                response = full_output.split("<|assistant|>")[-1].strip()
            else:
                # último recurso: retorna a saída completa (replace(prompt) é frágil após skip_special_tokens)
                response = full_output.strip()
        
        return self._clean_response(response)
    #-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    # método para processar múltiplos prompts em batch
    def _call_model_batch(self, prompts: List[str]) -> List[str]:
        """
        Processa múltiplos prompts em batch (TRUE BATCH INFERENCE)

        Args:
            prompts: Lista de prompts individuais por frame (sem summary)

        Returns:
            Lista de explicações geradas
        """

        # verifica se a lista de prompts está vazia para evitar processamento desnecessário e erros 
        if not prompts:
            return []
        
        logger.info(f"Phi-3 batch processing {len(prompts)} prompts...")
        
        # Tokeniza todos os prompts com padding

        t0 = time.time() # marca o início da tokenização para medir o tempo gasto nessa etapa

        # tokeniza o prompt, convertendo o texto em uma sequência de tokens numéricos que o modelo pode entender 
        # aplica padding para garantir que todos os prompts tenham o mesmo comprimento, permitindo o processamento em batch
        inputs = self.tokenizer(
            prompts,
            return_tensors="pt",
            truncation=True,
            max_length=512,
            padding=True,              # Padding para alinhar tamanhos
            return_attention_mask=True # Garante que o modelo ignore os tokens de padding durante a geração, mantendo a eficiência/qualidade das respostas mesmo com prompts de comprimentos variados
        )
        
        # Move para device do modelo - CPU ou GPU
        device = next(self.model.parameters()).device
        inputs = {k: v.to(device) for k, v in inputs.items()}

        t1 = time.time() # marca o fim da tokenização para calcular o tempo gasto nessa etapa

        logger.debug(f"Batch tokenization: {(t1-t0)*1000:.1f}ms for {len(prompts)} prompts")

        # Geração em batch
        with torch.inference_mode():
            t2 = time.time() # marca o início da geração para medir o tempo gasto nessa etapa

            # gera as respostas para todos os prompts em paralelo, otimizando o tempo de inferência quando há múltiplos frames a serem processados
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=self.max_tokens,
                temperature=self.temperature,
                top_p=self.top_p,
                do_sample=True if self.temperature > 0 else False,
                pad_token_id=self.tokenizer.pad_token_id,
                eos_token_id=self.tokenizer.eos_token_id
            )

            t3 = time.time() # marca o fim da geração para calcular o tempo gasto nessa etapa

            # calcula o número total de tokens gerados para todos os prompts
            # subtraindo o comprimento dos tokens de entrada do comprimento total dos tokens de saída para cada prompt
            total_tokens = sum(len(outputs[i]) - len(inputs['input_ids'][i]) for i in range(len(prompts)))

            # calcula a média de tokens gerados por prompt para fornecer uma métrica de eficiência da geração em batch
            avg_tokens = total_tokens / len(prompts)

            logger.info(f"Batch generation: {(t3-t2):.2f}s ({len(prompts)} prompts, avg {avg_tokens:.0f} tokens, {(t3-t2)/len(prompts):.2f}s/prompt)")

        # Decodifica cada resposta
        t4 = time.time() # marca o início da decodificação para medir o tempo gasto nessa etapa

        # lista para armazenar as respostas geradas para cada prompt
        responses = [] 

        # itera sobre cada saída gerada e seus tokens de entrada correspondentes para processar cada resposta individualmente
        for output, input_ids in zip(outputs, inputs['input_ids']): 
            # Decodifica apenas os tokens novos
            input_length = len(input_ids)                                                        # comprimento dos tokens de entrada para identificar onde começa a resposta gerada
            generated_tokens = output[input_length:]                                             # extrai apenas os tokens gerados para o prompt atual
            response = self.tokenizer.decode(generated_tokens, skip_special_tokens=True).strip() # decodifica os tokens gerados para texto
            
            # Fallback se extração falhar
            if not response or len(response) < 10:
                full_output = self.tokenizer.decode(output, skip_special_tokens=True)
                if "<|assistant|>" in full_output:
                    response = full_output.split("<|assistant|>")[-1].strip()
                else:
                    response = full_output.strip()
            
            responses.append(self._clean_response(response))

        t5 = time.time() # marca o fim da decodificação para calcular o tempo gasto nessa etapa

        logger.debug(f"Batch decoding: {(t5-t4)*1000:.1f}ms")
        logger.info(f"Phi-3 batch completed: {len(responses)} responses")
        
        return responses
