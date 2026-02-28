"""
Qwen 0.5B Model Implementation - MVP Illumination Only
Otimizado para Jetson (baixa latência, mínima VRAM)
"""

import logging
from typing import Dict, List
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

from app.models.base_model import ARDiagnosticModel
from app.config.config import Config

logger = logging.getLogger(__name__)


class QwenARModel(ARDiagnosticModel):
    """
    Implementação com Qwen 2.5 0.5B Instruct
    
    Características:
    - 0.5B parâmetros (muito leve)
    - ~1GB VRAM com quantização 4-bit
    - ~1.2s por cena (GPU)
    - Ideal para Jetson Nano/Xavier NX
    """
    
    MODEL_NAME = "Qwen/Qwen2.5-0.5B-Instruct"
    
    def __init__(self, use_4bit: bool = True, device: str = None):
        """
        Inicializa modelo Qwen
        
        Args:
            use_4bit: Usar quantização 4-bit (recomendado)
            device: 'cuda', 'cpu', ou 'auto' (auto-detecta se None)
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
        self.max_tokens = config.get('models.qwen.max_tokens', 100)
        self.temperature = config.get('models.qwen.temperature', 0.3)
        self.top_p = config.get('models.qwen.top_p', 0.85)
        
        logger.info(f"Generation params: max_tokens={self.max_tokens}, temp={self.temperature}, top_p={self.top_p}")
        
        # Carrega modelo
        self._load_model()
    
    def _load_model(self):
        """Carrega Qwen 0.5B com otimizações"""
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
                    trust_remote_code=True,
                    torch_dtype=torch.float16
                )
                logger.info("Model loaded with 4-bit quantization")
            else:
                # CPU ou sem quantização
                self.model = AutoModelForCausalLM.from_pretrained(
                    self.MODEL_NAME,
                    device_map="auto",
                    trust_remote_code=True,
                    torch_dtype=torch.float32 if self.device == 'cpu' else torch.float16
                )
                logger.info(f"Model loaded on {self.device}")
            
            # Carrega tokenizer
            self.tokenizer = AutoTokenizer.from_pretrained(
                self.MODEL_NAME,
                trust_remote_code=True
            )
            
            # Configura pad token
            if self.tokenizer.pad_token is None:
                self.tokenizer.pad_token = self.tokenizer.eos_token
            
            logger.info("Qwen 0.5B loaded successfully")
            
        except Exception as e:
            logger.error(f"Error loading model: {e}")
            raise
    
    def _build_prompt(self, metrics: Dict, status: str, risk_level: str,
                     triggered_rules: List[str]) -> str:
        """Constrói prompt para Qwen (ChatML format)"""
        
        # System prompt - específico sobre iluminação
        system_msg = (
            "You are an AR lighting specialist. Analyze the illumination conditions and explain "
            "how they affect AR tracking, object recognition, and user experience. "
            "Be specific about lighting quality factors like brightness, contrast, and uniformity. "
            "Provide a complete, natural explanation in 2-3 sentences. Stay factual and technical."
        )
        
        # Extrai evidências
        illumination_label = metrics.get('illumination_label', 'unknown')
        illumination_score = metrics.get('illumination', 0.0)
        mean_luma = metrics.get('mean_luma', 0.0)
        uniformity = metrics.get('uniformity', 0.0)
        
        # User prompt
        if status == 'pass':
            user_msg = (
                f"Lighting Analysis:\n"
                f"- Quality: {illumination_label.upper()}\n"
                f"- Illumination Score: {illumination_score:.2f}\n"
                f"- Mean Brightness: {mean_luma:.1f}/255\n"
                f"- Uniformity: {uniformity:.2f}\n"
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
                f"Status: FAIL\n"
                f"Problems Detected: {rules_text}\n\n"
                f"Explain how these lighting issues specifically impact AR tracking accuracy and visual quality:"
            )
        
        # Formato ChatML para Qwen
        messages = [
            {"role": "system", "content": system_msg},
            {"role": "user", "content": user_msg}
        ]
        
        # Aplica template do tokenizer
        prompt = self.tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True
        )
        
        return prompt
    
    def _call_model(self, prompt: str) -> str:
        """Gera explicação com Qwen"""
        import time
        
        # Tokeniza
        t0 = time.time()
        inputs = self.tokenizer(
            prompt,
            return_tensors="pt",
            truncation=True,
            max_length=512
        ).to(self.model.device)
        t1 = time.time()
        logger.debug(f"Tokenização: {(t1-t0)*1000:.1f}ms")
        
        # Gera com parâmetros otimizados para velocidade
        with torch.no_grad():
            t2 = time.time()
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=self.max_tokens,
                temperature=self.temperature,
                top_p=self.top_p,
                do_sample=True if self.temperature > 0 else False,
                repetition_penalty=1.05,
                pad_token_id=self.tokenizer.pad_token_id,
                eos_token_id=self.tokenizer.eos_token_id
            )
            t3 = time.time()
            num_tokens = outputs[0].shape[0] - inputs['input_ids'].shape[1]
            logger.info(f"Geração LLM: {(t3-t2):.2f}s ({num_tokens} tokens gerados)")
        
        # Decodifica
        t4 = time.time()
        full_output = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        t5 = time.time()
        logger.debug(f"Decodificação: {(t5-t4)*1000:.1f}ms")
        
        # Extrai apenas a resposta
        if "<|im_start|>assistant" in full_output:
            explanation = full_output.split("<|im_start|>assistant")[-1].strip()
        elif "assistant" in full_output:
            explanation = full_output.split("assistant")[-1].strip()
        else:
            if "one paragraph:" in full_output:
                explanation = full_output.split("one paragraph:")[-1].strip()
            else:
                parts = full_output.split("\n\n")
                explanation = parts[-1].strip() if len(parts) > 1 else full_output
        
        # Remove marcadores residuais
        explanation = explanation.replace("<|im_end|>", "").strip()
        
        return explanation
