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
    
    def __init__(self, use_4bit: bool = True, device: str = None, enable_compile: bool = False):
        """
        Inicializa modelo Qwen
        
        Args:
            use_4bit: Usar quantização 4-bit (recomendado)
            device: 'cuda', 'cpu', ou 'auto' (auto-detecta se None)
            enable_compile: Usar torch.compile() para aceleração (experimental)
        """
        super().__init__(use_4bit)
        
        self.enable_compile = enable_compile
        
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
            
            # Otimização: torch.compile() para aceleração (PyTorch 2.0+)
            if self.enable_compile and hasattr(torch, 'compile'):
                try:
                    logger.info("Compiling model with torch.compile()...")
                    self.model = torch.compile(self.model, mode="reduce-overhead")
                    logger.info("✅ Model compiled successfully")
                except Exception as e:
                    logger.warning(f"torch.compile() failed: {e}, continuing without compilation")
            
            # Otimização: BetterTransformer (integrado no transformers)
            # Nota: NÃO é compatível com modelos quantizados (bitsandbytes 4-bit)
            # Apenas tenta se NÃO estiver usando quantização 4-bit
            if not self.use_4bit and not self.enable_compile:
                try:
                    logger.info("Applying BetterTransformer optimization...")
                    self.model.to_bettertransformer()
                    logger.info("✅ BetterTransformer enabled")
                except AttributeError:
                    logger.debug("BetterTransformer not available in this transformers version")
                except Exception as e:
                    logger.debug(f"BetterTransformer failed: {e}")
            
            # Carrega tokenizer
            self.tokenizer = AutoTokenizer.from_pretrained(
                self.MODEL_NAME,
                trust_remote_code=True,
                padding_side='left'  # Requerido para decoder-only em batch
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
            "Keep your explanation under 50 words. Stay factual and technical."
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
    
    def _build_summary_prompt(self, agg: Dict) -> str:
        """Constrói prompt de sumarização do ambiente (ChatML format)"""
        total          = agg['total']
        problem_count  = agg['problem_count']
        dominant_label = agg['dominant_label']
        overall_risk   = agg['overall_risk']
        avg_luma       = agg['avg_mean_luma']
        avg_uniformity = agg['avg_uniformity']
        avg_clip_bright = agg['avg_pct_clipped_bright']
        avg_clip_dark   = agg['avg_pct_clipped_dark']

        system_msg = (
            "You are an AR lighting specialist. Given aggregated illumination data from multiple "
            "frames of the same environment, provide a consolidated assessment. Explain the overall "
            "lighting conditions and their impact on AR tracking. Keep the assessment under 60 words. "
            "Stay factual and technical."
        )

        status_text = "FAIL" if problem_count > 0 else "PASS"
        user_msg = (
            f"Environment Assessment ({problem_count}/{total} frames problematic):\n"
            f"- Dominant lighting condition: {dominant_label.upper()}\n"
            f"- Overall risk: {overall_risk.upper()}\n"
            f"- Average brightness: {avg_luma:.1f}/255\n"
            f"- Average uniformity: {avg_uniformity:.2f}\n"
            f"- Average bright clipping: {avg_clip_bright:.1%}\n"
            f"- Average dark clipping: {avg_clip_dark:.1%}\n"
            f"Status: {status_text}\n\n"
            f"Provide a consolidated assessment of this environment for AR use and key recommendations:"
        )

        messages = [
            {"role": "system", "content": system_msg},
            {"role": "user",   "content": user_msg}
        ]

        prompt = self.tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True
        )
        return prompt

    def _call_model(self, prompt: str) -> str:
        """Gera explicação com Qwen (otimizado)"""
        import time
        
        # Tokeniza
        t0 = time.time()
        inputs = self.tokenizer(
            prompt,
            return_tensors="pt",
            truncation=True,
            max_length=512
        )
        
        # Move para device do modelo
        device = next(self.model.parameters()).device
        inputs = {k: v.to(device) for k, v in inputs.items()}
        t1 = time.time()
        logger.debug(f"Tokenização: {(t1-t0)*1000:.1f}ms")
        
        # Gera com parâmetros otimizados
        # torch.inference_mode() é mais rápido que torch.no_grad()
        with torch.inference_mode():
            t2 = time.time()
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=self.max_tokens,
                temperature=self.temperature,
                top_p=self.top_p,
                do_sample=True if self.temperature > 0 else False,
                pad_token_id=self.tokenizer.pad_token_id,
                eos_token_id=self.tokenizer.eos_token_id
            )
            t3 = time.time()
            num_tokens = outputs[0].shape[0] - inputs['input_ids'].shape[1]
            logger.info(f"Geração LLM: {(t3-t2):.2f}s ({num_tokens} tokens)")
        
        # Decodifica APENAS os tokens novos (otimização crítica)
        t4 = time.time()
        input_length = inputs['input_ids'].shape[1]
        generated_tokens = outputs[0][input_length:]
        response = self.tokenizer.decode(generated_tokens, skip_special_tokens=True).strip()
        t5 = time.time()
        logger.debug(f"Decodificação: {(t5-t4)*1000:.1f}ms")
        
        # Fallback se extração falhar
        if not response or len(response) < 10:
            full_output = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            if "<|im_start|>assistant" in full_output:
                response = full_output.split("<|im_start|>assistant")[-1].strip()
                if "<|im_end|>" in response:
                    response = response.split("<|im_end|>")[0].strip()
            else:
                response = full_output.replace(prompt, "").strip()
        
        return response
    
    def _call_model_batch(self, prompts: List[str]) -> List[str]:
        """
        Processa múltiplos prompts em batch (TRUE BATCH INFERENCE)
        Múltiplos forward passes em paralelo
        
        Args:
            prompts: Lista de prompts
        
        Returns:
            Lista de explicações geradas
        """
        import time
        
        if not prompts:
            return []
        
        logger.info(f"Batch processing {len(prompts)} prompts...")
        
        # Tokeniza todos os prompts com padding
        t0 = time.time()
        inputs = self.tokenizer(
            prompts,
            return_tensors="pt",
            truncation=True,
            max_length=512,
            padding=True,  # Padding para alinhar tamanhos
            return_attention_mask=True
        )
        
        # Move para device do modelo
        device = next(self.model.parameters()).device
        inputs = {k: v.to(device) for k, v in inputs.items()}
        t1 = time.time()
        logger.debug(f"Batch tokenization: {(t1-t0)*1000:.1f}ms for {len(prompts)} prompts")
        
        # Geração em batch
        # torch.inference_mode() é mais rápido que torch.no_grad()
        with torch.inference_mode():
            t2 = time.time()
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=self.max_tokens,
                temperature=self.temperature,
                top_p=self.top_p,
                do_sample=True if self.temperature > 0 else False,
                pad_token_id=self.tokenizer.pad_token_id,
                eos_token_id=self.tokenizer.eos_token_id
            )
            t3 = time.time()
            total_tokens = sum(len(outputs[i]) - len(inputs['input_ids'][i]) for i in range(len(prompts)))
            avg_tokens = total_tokens / len(prompts)
            logger.info(f"Batch generation: {(t3-t2):.2f}s ({len(prompts)} prompts, avg {avg_tokens:.0f} tokens, {(t3-t2)/len(prompts):.2f}s/prompt)")
        
        # Decodifica cada resposta
        t4 = time.time()
        responses = []
        for i, (output, input_ids) in enumerate(zip(outputs, inputs['input_ids'])):
            # Decodifica apenas os tokens novos
            input_length = len(input_ids)
            generated_tokens = output[input_length:]
            response = self.tokenizer.decode(generated_tokens, skip_special_tokens=True).strip()
            
            # Fallback se extração falhar
            if not response or len(response) < 10:
                full_output = self.tokenizer.decode(output, skip_special_tokens=True)
                if "<|im_start|>assistant" in full_output:
                    response = full_output.split("<|im_start|>assistant")[-1].strip()
                    if "<|im_end|>" in response:
                        response = response.split("<|im_end|>")[0].strip()
                else:
                    response = full_output.strip()
            
            responses.append(response)
        
        t5 = time.time()
        logger.debug(f"Batch decoding: {(t5-t4)*1000:.1f}ms")
        
        return responses
