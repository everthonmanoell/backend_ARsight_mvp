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
        
        # System prompt - restritivo para reduzir alucinações
        system_msg = (
            "You are an AR diagnostic expert. Analyze ONLY the provided illumination metric. "
            "Provide a factual, technical explanation based strictly on the data shown. "
            "Use one concise paragraph. Do NOT invent information."
        )
        
        # Extrai evidências
        illumination_label = metrics.get('illumination_label', 'unknown')
        illumination_score = metrics.get('illumination', 0.0)
        
        # User prompt
        if status == 'pass':
            user_msg = (
                f"Scene Analysis:\n"
                f"- Illumination: {illumination_label} (score: {illumination_score:.2f})\n"
                f"Status: PASS (good conditions)\n\n"
                f"Explain why this scene is suitable for AR in one paragraph:"
            )
        else:
            rules_text = '; '.join(triggered_rules)
            user_msg = (
                f"Scene Analysis:\n"
                f"- Illumination: {illumination_label} (score: {illumination_score:.2f})\n"
                f"Status: FAIL\n"
                f"Issues: {rules_text}\n\n"
                f"Explain the critical problems affecting AR performance in one paragraph:"
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
        
        # Tokeniza
        inputs = self.tokenizer(
            prompt,
            return_tensors="pt",
            truncation=True,
            max_length=512
        ).to(self.model.device)
        
        # Gera com parâmetros anti-alucinação
        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=self.max_tokens,
                temperature=self.temperature,
                top_p=self.top_p,
                do_sample=True if self.temperature > 0 else False,
                repetition_penalty=1.1,  # Evita loops
                no_repeat_ngram_size=3,  # Evita repetições
                pad_token_id=self.tokenizer.pad_token_id,
                eos_token_id=self.tokenizer.eos_token_id
            )
        
        # Decodifica
        full_output = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        
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
