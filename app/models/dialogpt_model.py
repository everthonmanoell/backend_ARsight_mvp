"""
Microsoft DialoGPT-small Model Implementation - Jetson Nano Optimized
Modelo muito leve (117M params) para Jetson Nano com PyTorch 1.10
"""

import logging
import time
from typing import Dict, List
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

from app.models.base_model import ARDiagnosticModel
from app.config.config import Config

logger = logging.getLogger(__name__)

class DialoGPTARModel(ARDiagnosticModel):
    """
    Implementação com Microsoft DialoGPT-small
    
    Características:
    - 117M parâmetros (ultra-leve)
    - ~500MB em FP32 / ~250MB em FP16
    - Compatível com Jetson Nano (PyTorch 1.10, transformers 4.8.2)
    - Modelo conversacional baseado em GPT-2
    """
    
    MODEL_NAME = "microsoft/DialoGPT-small"  # Default (override via YAML)
    
    def __init__(self, use_4bit: bool = False, device: str = None):
        """
        Inicializa modelo DialoGPT-small
        
        Args:
            use_4bit: Ignorado (DialoGPT é tão pequeno que quantização não é necessária)
            device: 'cuda', 'cpu', ou 'auto' (auto-detecta se None)
        """
        super().__init__(use_4bit=False)
        
        # Detecta dispositivo
        if device is None or device == 'auto':
            self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        else:
            self.device = device
        
        logger.info(f"Using device: {self.device}")
        
        # Carrega configurações de geração do YAML
        config = Config()
        
        # Lê a versão específica do DialoGPT do YAML
        # Padrão: microsoft/DialoGPT-small (override via config YAML)
        self.model_name = config.get('models.dialogpt-small.name', self.MODEL_NAME)
        logger.info(f"DialoGPT model version from config: {self.model_name}")
        
        self.max_tokens = config.get('models.dialogpt-small.max_tokens', 40)
        self.summary_max_tokens = config.get('models.dialogpt-small.summary_tokens', 60)
        
        # Temperatura
        self.temperature = config.get('models.dialogpt-small.temperature', 0.3)
        
        # Top-p
        self.top_p = config.get('models.dialogpt-small.top_p', 0.85)
        
        # Greedy decoding: velocidade máxima em Jetson
        self.greedy_decoding = config.get('models.greedy_decoding', True)
        
        # Prompt max length: DialoGPT usa contexto menor
        self.prompt_max_length = config.get('models.prompt_max_length', 256)
        
        logger.info(
            f"Generation params: max_tokens={self.max_tokens}, summary_max_tokens={self.summary_max_tokens}, "
            f"temp={self.temperature}, top_p={self.top_p}, greedy={self.greedy_decoding}, "
            f"prompt_max_length={self.prompt_max_length}"
        )
        
        # Carrega modelo
        self._load_model()
    
    #---------------------------------------------------------------------
    def _load_model(self):
        """Carrega DialoGPT-small com otimizações para Jetson"""
        
        logger.info(f"Loading {self.model_name}...")
        
        try:
            # 🔍 PRE-LOAD DEBUG
            logger.info(f"🔍 PRE-LOAD: CUDA available = {torch.cuda.is_available()}")
            if torch.cuda.is_available():
                logger.info(f"🔍 PRE-LOAD: CUDA device = {torch.cuda.get_device_name(0)}")
                logger.info(f"🔍 PRE-LOAD: Device properties = compute {torch.cuda.get_device_capability(0)}")
            
            # ⚠️ CRÍTICO: Jetson Nano (torch 1.10) - NÃO usar device_map="auto"
            logger.info(f"🔍 Loading model from {self.model_name}...")
            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_name,
                trust_remote_code=False,  # DialoGPT não precisa de remote code
                torch_dtype=torch.float32 if self.device == 'cpu' else torch.float16,
            )
            
            # 🔍 DEBUG POST-LOAD
            try:
                first_param = next(self.model.parameters())
                logger.info(f"🔍 POST-LOAD (before .to()): device = {first_param.device}, dtype = {first_param.dtype}")
            except Exception as e:
                logger.warning(f"⚠️  Could not get first param: {e}")
            
            # CRÍTICO: Move explícito para device
            logger.info(f"🔍 Moving model to {self.device}...")
            self.model = self.model.to(self.device)
            
            # 🔍 DEBUG POST-MOVE
            try:
                first_param = next(self.model.parameters())
                actual_device = str(first_param.device)
                if "cuda" in self.device and "cpu" in actual_device:
                    logger.error(f"❌ CRITICAL: Model is on {actual_device} but expected {self.device}!")
                logger.info(f"✅ POST-MOVE: device = {first_param.device}, dtype = {first_param.dtype}")
            except Exception as e:
                logger.warning(f"⚠️  Could not verify device placement: {e}")
            
            # Log VRAM
            if self.device == 'cuda':
                logger.info(f"🔍 VRAM after .to(cuda): {torch.cuda.memory_allocated() / 1e9:.2f} GB allocated")
                logger.info(f"🔍 Total VRAM: {torch.cuda.get_device_properties(0).total_memory / 1e9:.2f} GB")
            
            # Modo de inferência
            self.model.eval()
            
            logger.info(f"✅ Model loaded successfully on {self.device}")
            
            # Carrega tokenizer
            logger.info(f"Loading tokenizer from {self.model_name}...")
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            
            # Set pad token se não existir
            if self.tokenizer.pad_token is None:
                self.tokenizer.pad_token = self.tokenizer.eos_token
                logger.info("Set pad_token to eos_token")
            
            logger.info("✅ DialoGPT-small model and tokenizer loaded successfully")
            
        except Exception as e:
            logger.error(f"❌ Failed to load DialoGPT model: {e}")
            raise

    #---------------------------------------------------------------------
    def _build_prompt(self, metrics: Dict, status: str, risk_level: str, triggered_rules: List[str]) -> str:
        """
        Constrói prompt específico para DialoGPT-small
        DialoGPT é um modelo conversacional simples — usa prompts mais naturais sem estrutura ChatML
        """
        
        import random
        
        # Extrai métricas
        illumination_label = metrics.get('illumination_label', 'unknown')
        illumination_score = metrics.get('illumination', 0.0)
        mean_luma = metrics.get('mean_luma', 0.0)
        uniformity = metrics.get('uniformity', 0.0)
        
        # Templates para PASS
        if status == 'pass':
            pass_templates = [
                f"Scene lighting analysis: {illumination_label} conditions detected. Brightness is {mean_luma:.0f}/255 with {uniformity:.0%} uniformity. This supports AR operations well.",
                f"Lighting diagnostic: {illumination_label} lighting (brightness {mean_luma:.0f}/255) detected. Scene uniformity {uniformity:.0%}. Suitable for AR.",
                f"The scene has {illumination_label} illumination. Measured brightness {mean_luma:.0f}/255. Uniformity {uniformity:.0%}. AR tracking conditions are adequate.",
                f"Illumination check: {illumination_label} reading confirmed. Brightness {mean_luma:.0f}/255, uniformity {uniformity:.0%}. Good for AR applications."
            ]
            prompt = random.choice(pass_templates)
        else:
            # Mapeia label para causa legível
            cause_map = {
                'overexposed': 'bright lighting causes reduced contrast and feature visibility',
                'underexposed': 'dim lighting creates increased noise and feature detection difficulty',
                'poor': 'uneven lighting creates inconsistent contrast across the scene'
            }
            cause = cause_map.get(illumination_label, 'compromised lighting degrades image quality')
            
            fail_templates = [
                f"Scene analysis shows {illumination_label} lighting at brightness {mean_luma:.0f}/255. Problem: {cause}. AR tracking affected.",
                f"Lighting diagnostic: {illumination_label} detected (brightness {mean_luma:.0f}/255). Issue: {cause}. Consider adjusting environment.",
                f"Scene illumination is {illumination_label} with brightness {mean_luma:.0f}/255. This causes {cause}. Affects AR performance.",
                f"Analysis: {illumination_label} lighting observed (brightness {mean_luma:.0f}/255). {cause.capitalize()}. Recommend correction."
            ]
            prompt = random.choice(fail_templates)
        
        return prompt
    
    #---------------------------------------------------------------------
    def _build_summary_prompt(self, agg: Dict) -> str:
        """
        Constrói prompt de sumarização para lote de frames (DialoGPT style)
        Detecta condições mistas (over + underexposed) para usar "inadequate" em vez da dominante
        """
        
        import random
        
        total = agg['total']
        problem_count = agg['problem_count']
        dominant_label = agg['dominant_label']
        label_breakdown = agg.get('label_breakdown', {})
        
        # Detecta se há condições mistas (tanto overexposed quanto underexposed)
        has_overexposed = label_breakdown.get('overexposed', 0) > 0
        has_underexposed = label_breakdown.get('underexposed', 0) > 0
        mixed_conditions = has_overexposed and has_underexposed
        
        # Se há condições mistas, usa "inadequate" em vez da etiqueta dominante
        if mixed_conditions:
            condition_label = 'inadequate'
        else:
            condition_label = dominant_label
        
        if problem_count > 0:
            summary_templates = [
                f"Batch analysis of {total} frames: {problem_count} frames show {condition_label} lighting. This impacts AR tracking quality in the batch.",
                f"Frame batch review ({total} total): {problem_count} frames detected with {condition_label} conditions. AR performance may be affected.",
                f"Summary of {total} analyzed frames: {problem_count} exhibit {condition_label} lighting. Recommendation: adjust environment for better AR conditions.",
                f"{total} frames analyzed. Issue detected in {problem_count} frames: {condition_label} lighting. Consider scene optimization."
            ]
            prompt = random.choice(summary_templates)
        else:
            summary_templates = [
                f"Batch analysis complete: all {total} frames show adequate lighting for AR applications.",
                f"Review of {total} frames confirms optimal lighting conditions throughout. AR tracking feasible.",
                f"Full batch analyzed ({total} frames) — no lighting issues detected. Scene ready for AR.",
                f"{total} frames checked with positive result: lighting is suitable for AR operations."
            ]
            prompt = random.choice(summary_templates)
        
        return prompt
    
    #---------------------------------------------------------------------
    def _postprocess_dialogpt_text(self, text: str) -> str:
        """
        Validação específica para DialoGPT-small
        Detecta e rejeita respostas conversacionais/alucinadas
        Retorna None se detect junk (trigga fallback para template)
        """
        import re
        
        text = text.strip()
        if not text:
            return None
        
        # CRITÉRIO 1: Rejeita respostas que terminam com "?"
        if text.endswith("?"):
            logger.warning(f"Rejected: Response is a question: {text[:60]}...")
            return None
        
        # CRITÉRIO 2: Rejeita perguntas interrogativas (What, How, Why, Where, When, Do, Can, etc)
        if re.match(r'^(what|how|why|where|when|do|can|is|are|would|could)\s', text.lower()):
            logger.warning(f"Rejected: Conversational question: {text[:60]}...")
            return None
        
        # CRITÉRIO 3: Rejeita respostas com padrão chat ("I would like", "I think you", "I'm not sure", "I have")
        chat_patterns = [
            r"\bi would like\b",
            r"\bi would\s+(recommend|suggest)",  # "I would recommend..." "I would suggest..."
            r"\bi think you\b",
            r"\bi think the\b",
            r"\bi'm not sure\b",
            r"\bi am not\b",
            r"\bi am a\b",
            r"\bI don't know\b",
            r"\bi have a\b",        # "I have a bright light..."
            r"\bi have the\b",      # "I have the..."
            r"\bi have been\b",     # "I have been..."
            r"\bwe have\b",         # "We have..."
        ]
        text_lower = text.lower()
        for pattern in chat_patterns:
            if re.search(pattern, text_lower):
                logger.warning(f"Rejected: Chat pattern detected: {text[:60]}...")
                return None
        
        # CRITÉRIO 4: Rejeita repetições de palavras-chave (ex: "brightness diagnostic. brightness diagnostic")
        # Detecta quando palavras principais se repetem muito
        words = text_lower.split()
        if len(words) > 2:
            word_counts = {}
            for word in words:
                word_counts[word] = word_counts.get(word, 0) + 1
            # Se alguma palavra aparece >3 vezes, é repetição excessiva
            if any(count > 3 for count in word_counts.values()):
                logger.warning(f"Rejected: Word repetition detected: {text[:60]}...")
                return None
        
        # CRITÉRIO 5: Rejeita repetições de tokens (AR.AR.AR.AR ou qualquer repetição >4)
        # Padrão: palavra seguida de ponto, repetida múltiplas vezes
        repeat_pattern = r'(\b\w+\.){4,}'
        if re.search(repeat_pattern, text):
            logger.warning(f"Rejected: Token repetition detected: {text[:60]}...")
            return None
        
        # CRITÉRIO 6: Rejeita sufixos ".I." ou ".I" ou ".I. e" (token de córte mal formatado)
        # Pode ter espaços e letras após
        if re.search(r'\.\s*I\.(\s+\w+)*\s*$', text):
            logger.warning(f"Rejected: Malformed token suffix '.I': {text[-20:]}...")
            return None
        
        # CRITÉRIO 7: Rejeita sufixos corrompidos (palavra comum + ponto no final)
        # Padrão: palavra comum tecnicamente (camera, device, light, system, etc) seguida de ponto no final da frase
        corrupted_suffixes = [
            r'\.camera\.?\s*$',
            r'\.device\.?\s*$',
            r'\.light\.?\s*$',
            r'\.system\.?\s*$',
            r'\.mode\.?\s*$',
            r'\.setting\.?\s*$',
            r'\.\w{4,}\.?\s*$'  # Qualquer palavra de 4+ chars seguida de ponto no final
        ]
        for suffix_pattern in corrupted_suffixes:
            if re.search(suffix_pattern, text_lower):
                logger.warning(f"Rejected: Corrupted suffix detected: {text[-30:]}...")
                return None
        
        # CRITÉRIO 8: Rejeita respostas que não mencionam contexto de iluminação
        # Resposta válida deve ter pelo menos uma palavra-chave relacionada
        illumination_keywords = [
            'light', 'lighting', 'illumination', 'brightness', 'bright', 'exposure',
            'exposed', 'underexposed', 'overexposed', 'shadow', 'dark', 'dim',
            'uniform', 'uniformity', 'feature', 'visibility', 'contrast', 'luma',
            'visual', 'detect', 'detection', 'tracking', 'ar', 'scene'
        ]
        has_context = any(keyword in text_lower for keyword in illumination_keywords)
        if not has_context:
            logger.warning(f"Rejected: No illumination context keywords: {text[:50]}...")
            return None
        
        return text
    
    #---------------------------------------------------------------------
    def _call_model(self, prompt: str, max_new_tokens: int = None) -> str:
        """
        Chama DialoGPT-small para gerar explicação (single prompt)
        """
        
        try:
            t0 = time.time()
            
            # Tokeniza prompt
            inputs = self.tokenizer(
                prompt,
                return_tensors='pt',
                padding=True,
                truncation=True,
                max_length=self.prompt_max_length
            )
            
            # Move para device
            device = next(self.model.parameters()).device
            inputs = {k: v.to(device) for k, v in inputs.items()}
            
            t1 = time.time()
            logger.debug(f"Tokenization: {(t1-t0)*1000:.1f}ms")
            
            # Gera
            with torch.inference_mode():
                t2 = time.time()
                
                use_sampling = (not self.greedy_decoding) and (self.temperature > 0)
                
                outputs = self.model.generate(
                    **inputs,
                    max_new_tokens=max_new_tokens if max_new_tokens is not None else self.max_tokens,
                    temperature=self.temperature if use_sampling else 1.0,
                    top_p=self.top_p if use_sampling else 1.0,
                    top_k=None if not use_sampling else 20,
                    do_sample=use_sampling,
                    pad_token_id=self.tokenizer.pad_token_id,
                    eos_token_id=self.tokenizer.eos_token_id
                )
                
                t3 = time.time()
                num_tokens = outputs[0].shape[0] - inputs['input_ids'].shape[1]
                logger.info(f"DialoGPT generation: {(t3-t2):.2f}s ({num_tokens} tokens)")
            
            # Decodifica apenas tokens novos
            t4 = time.time()
            input_length = inputs['input_ids'].shape[1]
            generated_tokens = outputs[0][input_length:]
            response = self.tokenizer.decode(generated_tokens, skip_special_tokens=True).strip()
            
            t5 = time.time()
            logger.debug(f"Decoding: {(t5-t4)*1000:.1f}ms")
            
            # Fallback se resposta vazia
            if not response or len(response) < 10:
                logger.warning("Empty response from model, using full output")
                response = self.tokenizer.decode(outputs[0], skip_special_tokens=True).strip()
            
            # Valida alucinações específicas do DialoGPT
            response = self._postprocess_dialogpt_text(response)
            if response is None:
                return ""  # Retorna vazio para ativar fallback de template
            
            return self._clean_response(response)
            
        except Exception as e:
            logger.error(f"Error in _call_model: {e}")
            raise
    
    #---------------------------------------------------------------------
    def _call_model_batch(self, prompts: List[str]) -> List[str]:
        """
        Processa múltiplos prompts em batch (TRUE BATCH INFERENCE)
        """
        
        if not prompts:
            return []
        
        logger.info(f"Batch processing {len(prompts)} prompts...")
        
        try:
            t0 = time.time()
            
            # Tokeniza com padding para batch
            inputs = self.tokenizer(
                prompts,
                return_tensors='pt',
                truncation=True,
                max_length=self.prompt_max_length,
                padding=True,
                return_attention_mask=True
            )
            
            # Move para device
            device = next(self.model.parameters()).device
            inputs = {k: v.to(device) for k, v in inputs.items()}
            
            t1 = time.time()
            logger.debug(f"Batch tokenization: {(t1-t0)*1000:.1f}ms for {len(prompts)} prompts")
            
            # Geração em batch
            with torch.inference_mode():
                t2 = time.time()
                
                use_sampling = (not self.greedy_decoding) and (self.temperature > 0)
                
                outputs = self.model.generate(
                    **inputs,
                    max_new_tokens=self.max_tokens,
                    temperature=self.temperature if use_sampling else 1.0,
                    top_p=self.top_p if use_sampling else 1.0,
                    top_k=None if not use_sampling else 20,
                    do_sample=use_sampling,
                    pad_token_id=self.tokenizer.pad_token_id,
                    eos_token_id=self.tokenizer.eos_token_id
                )
                
                t3 = time.time()
                total_tokens = sum(len(outputs[i]) - len(inputs['input_ids'][i]) for i in range(len(prompts)))
                avg_tokens = total_tokens / len(prompts) if prompts else 0
                logger.info(f"Batch generation: {(t3-t2):.2f}s ({len(prompts)} prompts, avg {avg_tokens:.0f} tokens)")
            
            # Decodifica respostas
            t4 = time.time()
            responses = []
            
            for output, input_ids in zip(outputs, inputs['input_ids']):
                input_length = len(input_ids)
                generated_tokens = output[input_length:]
                response = self.tokenizer.decode(generated_tokens, skip_special_tokens=True).strip()
                
                # Fallback se vazio
                if not response or len(response) < 10:
                    response = self.tokenizer.decode(output, skip_special_tokens=True).strip()
                
                # Valida alucinações específicas do DialoGPT
                response = self._postprocess_dialogpt_text(response)
                if response is None:
                    response = ""  # Vazio para ativar fallback de template
                else:
                    response = self._clean_response(response)
                
                responses.append(response)
            
            t5 = time.time()
            logger.debug(f"Batch decoding: {(t5-t4)*1000:.1f}ms")
            
            return responses
            
        except Exception as e:
            logger.error(f"Error in _call_model_batch: {e}")
            raise
