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
    - ~1.8s por cena (GPU)
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
        self.temperature = config.get('models.phi.temperature', 0.4)
        self.top_p = config.get('models.phi.top_p', 0.85)
        
        logger.info(f"Generation params: max_tokens={self.max_tokens}, temp={self.temperature}, top_p={self.top_p}")
        
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
                    trust_remote_code=True,
                    torch_dtype=torch.float16,
                    attn_implementation="eager"  # Fix para rope_scaling KeyError
                )
            else:
                self.model = AutoModelForCausalLM.from_pretrained(
                    self.MODEL_NAME,
                    device_map="auto",
                    trust_remote_code=True,
                    torch_dtype=torch.float32 if self.device == 'cpu' else torch.float16,
                    attn_implementation="eager"  # Fix para rope_scaling KeyError
                )
            
            self.tokenizer = AutoTokenizer.from_pretrained(
                self.MODEL_NAME,
                trust_remote_code=True
            )
            
            if self.tokenizer.pad_token is None:
                self.tokenizer.pad_token = self.tokenizer.eos_token
            
            logger.info("Phi-3 Mini loaded successfully")
            
        except Exception as e:
            logger.error(f"Error loading model: {e}")
            raise
    
    def _build_prompt(self, metrics: Dict, status: str, risk_level: str,
                     triggered_rules: List[str]) -> str:
        """Constrói prompt para Phi-3"""
        
        system_msg = (
            "You are an AR diagnostic expert. Analyze ONLY the provided illumination metric. "
            "Provide a factual, technical explanation. Use one concise paragraph."
        )
        
        # Extrai evidências
        illumination_label = metrics.get('illumination_label', 'unknown')
        illumination_score = metrics.get('illumination', 0.0)
        
        if status == 'pass':
            user_msg = (
                f"Analyze this AR scene (PASS status):\n"
                f"Illumination: {illumination_label} (score: {illumination_score:.2f})\n\n"
                f"Explain in one paragraph why conditions are favorable for AR:"
            )
        else:
            rules_text = '; '.join(triggered_rules)
            user_msg = (
                f"Analyze this AR scene (FAIL status):\n"
                f"Illumination: {illumination_label} (score: {illumination_score:.2f})\n"
                f"Critical issues: {rules_text}\n\n"
                f"Explain in one paragraph the problems affecting AR performance:"
            )
        
        # Phi-3 usa formato específico
        prompt = f"<|system|>\n{system_msg}<|end|>\n<|user|>\n{user_msg}<|end|>\n<|assistant|>\n"
        
        return prompt
    
    def _call_model(self, prompt: str) -> str:
        """Gera explicação com Phi-3"""
        inputs = self.tokenizer(
            prompt,
            return_tensors="pt",
            truncation=True,
            max_length=512
        ).to(self.model.device)
        
        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=self.max_tokens,
                temperature=self.temperature,
                top_p=self.top_p,
                do_sample=True if self.temperature > 0 else False,
                repetition_penalty=1.1,
                no_repeat_ngram_size=3,
                pad_token_id=self.tokenizer.pad_token_id,
                eos_token_id=self.tokenizer.eos_token_id
            )
        
        full_output = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        
        # Extrai resposta após <|assistant|>
        if "<|assistant|>" in full_output:
            explanation = full_output.split("<|assistant|>")[-1].strip()
        else:
            explanation = full_output.split("\n\n")[-1].strip()
        
        return explanation
