"""
Phi-3 Mini Model Implementation - MVP Illumination Only
Modelo alternativo com maior qualidade
"""

import logging
from typing import Dict, List
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

from app.models.base_model import ARDiagnosticModel
from app.config.config import Config

logger = logging.getLogger(__name__)


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
        
        if device is None or device == 'auto':
            self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        else:
            self.device = device
        
        logger.info(f"Using device: {self.device}")
        
        # Carrega configurações de geração do YAML
        config = Config()
        self.max_tokens = config.get('models.phi.max_tokens', 120)
        self.summary_max_tokens = config.get('models.phi.summary_tokens', 200)
        self.temperature = config.get('models.phi.temperature', 0.4)
        self.top_p = config.get('models.phi.top_p', 0.85)
        
        logger.info(f"Generation params: max_tokens={self.max_tokens}, summary_max_tokens={self.summary_max_tokens}, temp={self.temperature}, top_p={self.top_p}")
        
        self._load_model()
    
    def _load_model(self):
        """Carrega Phi-3 Mini"""
        logger.info(f"Loading {self.MODEL_NAME}...")
        
        try:
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
                    attn_implementation="eager"
                )
            else:
                self.model = AutoModelForCausalLM.from_pretrained(
                    self.MODEL_NAME,
                    device_map="auto",
                    dtype=torch.float32 if self.device == 'cpu' else torch.float16,
                    attn_implementation="eager"
                )
            
            self.tokenizer = AutoTokenizer.from_pretrained(
                self.MODEL_NAME
            )
            
            if self.tokenizer.pad_token is None:
                self.tokenizer.pad_token = self.tokenizer.eos_token
            
            # Essencial para batch inference com decoder-only models
            self.tokenizer.padding_side = 'left'

            # Phi-3 termina respostas com <|end|> — incluir como EOS token
            end_token_id = self.tokenizer.convert_tokens_to_ids("<|end|>")
            eos_id = self.tokenizer.eos_token_id
            self.eos_token_ids = list({eos_id, end_token_id}) if end_token_id != eos_id else [eos_id]
            
            logger.info("Phi-3 Mini loaded successfully")
            
        except Exception as e:
            logger.error(f"Error loading model: {e}")
            raise
    
    def _build_prompt(self, metrics: Dict, status: str, risk_level: str,
                     triggered_rules: List[str]) -> str:
        """Constrói prompt para Phi-3"""
        
        system_msg = (
            "You are an AR lighting specialist. Analyze the illumination conditions and explain "
            "how they affect AR tracking and user experience. "
            "Be factual and concise. Write exactly 1-2 sentences, under 50 words total. "
            "Do not use bullet points or lists."
        )
        
        # Extrai evidências
        illumination_label = metrics.get('illumination_label', 'unknown')
        illumination_score = metrics.get('illumination', 0.0)
        mean_luma = metrics.get('mean_luma', 0.0)
        uniformity = metrics.get('uniformity', 0.0)
        
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
        
        # Phi-3 usa formato específico
        prompt = f"<|system|>\n{system_msg}<|end|>\n<|user|>\n{user_msg}<|end|>\n<|assistant|>\n"
        
        return prompt
    
    def _build_summary_prompt(self, agg: Dict) -> str:
        """Constrói prompt de sumarização do ambiente (formato Phi-3)"""
        total           = agg['total']
        problem_count   = agg['problem_count']
        dominant_label  = agg['dominant_label']
        overall_risk    = agg['overall_risk']
        avg_luma        = agg['avg_mean_luma']
        avg_uniformity  = agg['avg_uniformity']
        avg_clip_bright = agg['avg_pct_clipped_bright']
        avg_clip_dark   = agg['avg_pct_clipped_dark']

        system_msg = (
            "You are an AR lighting specialist. Write in plain, natural sentences. "
            "Do not use bullet points, lists, or markdown formatting. "
            "Do not repeat the input data — interpret it and explain what it means for AR use. "
            "Keep your response to 1-2 sentences, under 40 words total."
        )

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

    def _clean_response(self, text: str) -> str:
        """Trunca na última frase completa para evitar cortes mid-sentence."""
        last_end = max(text.rfind('.'), text.rfind('!'), text.rfind('?'))
        if last_end > 20:  # Garante que haja conteúdo mínimo
            return text[:last_end + 1].strip()
        return text.strip()

    def _call_model(self, prompt: str, max_new_tokens: int = None) -> str:
        """Gera explicação com Phi-3 (otimizado)"""
        inputs = self.tokenizer(
            prompt,
            return_tensors="pt",
            truncation=True,
            max_length=512
        )
        
        # Move para device do modelo
        device = next(self.model.parameters()).device
        inputs = {k: v.to(device) for k, v in inputs.items()}
        
        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=max_new_tokens if max_new_tokens is not None else self.max_tokens,
                temperature=self.temperature,
                top_p=self.top_p,
                do_sample=True if self.temperature > 0 else False,
                pad_token_id=self.tokenizer.pad_token_id,
                eos_token_id=self.eos_token_ids
            )
        
        # Decodifica apenas novos tokens
        input_length = inputs['input_ids'].shape[1]
        generated_tokens = outputs[0][input_length:]
        response = self.tokenizer.decode(generated_tokens, skip_special_tokens=True).strip()
        
        # Fallback se extração falhar
        if not response or len(response) < 10:
            full_output = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            if "<|assistant|>" in full_output:
                response = full_output.split("<|assistant|>")[-1].strip()
            else:
                # último recurso: retorna a saída completa (replace(prompt) é frágil após skip_special_tokens)
                response = full_output.strip()
        
        return self._clean_response(response)
    
    def _call_model_batch(self, prompts: List[str]) -> List[str]:
        """
        Processa múltiplos prompts em batch (TRUE BATCH INFERENCE)

        Args:
            prompts: Lista de prompts individuais por frame (sem summary)

        Returns:
            Lista de explicações geradas
        """
        if not prompts:
            return []
        
        logger.info(f"Phi-3 batch processing {len(prompts)} prompts...")
        
        # Tokeniza todos os prompts com padding
        inputs = self.tokenizer(
            prompts,
            return_tensors="pt",
            truncation=True,
            max_length=512,
            padding=True,
            return_attention_mask=True
        )
        
        # Move para device do modelo
        device = next(self.model.parameters()).device
        inputs = {k: v.to(device) for k, v in inputs.items()}
        
        # Geração em batch
        with torch.inference_mode():
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=self.max_tokens,
                temperature=self.temperature,
                top_p=self.top_p,
                do_sample=True if self.temperature > 0 else False,
                pad_token_id=self.tokenizer.pad_token_id,
                eos_token_id=self.eos_token_ids
            )
        
        # Decodifica cada resposta
        responses = []
        for i, (output, input_ids) in enumerate(zip(outputs, inputs['input_ids'])):
            input_length = len(input_ids)
            generated_tokens = output[input_length:]
            response = self.tokenizer.decode(generated_tokens, skip_special_tokens=True).strip()
            
            # Fallback
            if not response or len(response) < 10:
                full_output = self.tokenizer.decode(output, skip_special_tokens=True)
                if "<|assistant|>" in full_output:
                    response = full_output.split("<|assistant|>")[-1].strip()
                else:
                    response = full_output.strip()
            
            responses.append(self._clean_response(response))
        
        logger.info(f"Phi-3 batch completed: {len(responses)} responses")
        return responses
