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
        Instrução direta (não pergunta) — evita modo "fórum de fotografia"
        """
        
        import random
        
        # Extrai métricas
        illumination_label = metrics.get('illumination_label', 'unknown')
        mean_luma = metrics.get('mean_luma', 0.0)
        uniformity = metrics.get('uniformity', 0.0)

        openers = [
            "AR lighting analysis.",
            "Scene lighting assessment.",
        ]

        if status == 'pass':
            prompts = [
                f"{random.choice(openers)} Conditions: {illumination_label}. "
                f"Brightness {mean_luma:.0f}/255, uniformity {uniformity:.0%}. "
                f"Write one short sentence saying this lighting supports AR tracking.",
                f"{random.choice(openers)} Brightness {mean_luma:.0f}, uniformity {uniformity:.0%}. "
                f"Describe in one sentence why this is good for AR.",
            ]
        else:
            prompts = [
                f"{random.choice(openers)} Conditions: {illumination_label}. "
                f"Brightness {mean_luma:.0f}/255, uniformity {uniformity:.0%}. "
                f"Write one short sentence saying this lighting harms AR tracking.",
                f"{random.choice(openers)} Brightness {mean_luma:.0f}, uniformity {uniformity:.0%}. "
                f"Describe in one sentence why this problematic for AR.",
            ]
        
        return random.choice(prompts)
    
    #---------------------------------------------------------------------
    def _build_summary_prompt(self, agg: Dict) -> str:
        """
        Summary é o texto principal da interface.
        Mantém variedade e naturalidade, mas sem abrir demais o modelo.
        Prefers framing com contexto de dados concretos.
        """
        import random

        total = agg['total']
        problem_count = agg['problem_count']
        dominant_label = agg['dominant_label']

        if problem_count > 0:
            prompts = [
                f"Frame batch review ({total} total): {problem_count} frames detected with {dominant_label} conditions. "
                f"Write one concise sentence about the AR impact.",
                f"Summary of {total} analyzed frames: {problem_count} exhibit {dominant_label} lighting. "
                f"Write one short sentence about how this affects AR tracking.",
                f"{total} frames analyzed. Issue detected in {problem_count} frames: {dominant_label} lighting. "
                f"Write one concise sentence summarizing the AR risk.",
                f"In this batch of {total} frames, {problem_count} show {dominant_label} lighting. "
                f"Describe in one short sentence the effect on AR performance.",
                f"Batch contains {total} frames with {problem_count} having {dominant_label} illumination. "
                f"Write one concise AR impact sentence.",
            ]
        else:
            prompts = [
                f"Batch analysis complete: all {total} frames show adequate lighting for AR applications. "
                f"Write one concise summary sentence.",
                f"Review of {total} frames confirms stable lighting conditions throughout. "
                f"Write one short sentence about AR readiness.",
                f"Full batch analyzed ({total} frames) with no lighting issues detected. "
                f"Write one concise sentence confirming AR suitability.",
                f"All {total} frames meet lighting requirements for stable AR tracking. "
                f"Write one short summary sentence.",
                f"{total} frames checked — consistent lighting throughout supports reliable AR performance. "
                f"Write one concise confirmation sentence.",
            ]

        return random.choice(prompts)
    
    #---------------------------------------------------------------------
    def _postprocess_dialogpt_text(self, text: str) -> str:
        """
        Limpeza de artefatos comuns em respostas de DialoGPT
        Valida contra:
        - Junk responses (contagens, meta-comentários)
        - Camera gear hallucinations (Canon, Nikon, lentes, etc)
        """
        import re
        
        text = text.strip()
        
        # Remove artefatos conhecidos
        text = text.replace("AR.I.", "AR.")
        text = text.replace("..", ".")
        
        # Detecta "junk responses" que indicam alucinação
        junk_indicators = [
            "I.",                    # Começo com "I."
            "edit formatting",       # Meta-comentário
            "formatting error",      # Meta-comentário
            "13 14 15 16 17",       # Contagem estranha
            "1,2, 3 and 4 5 7",     # Números soltos
            "Lightpassing",          # Não-palavra
        ]
        
        # Se detectar junk, retorna None para ativar fallback
        for indicator in junk_indicators:
            if indicator in text:
                logger.warning(f"Detected junk indicator '{indicator}' in response: {text[:60]}...")
                return None
        
        # Detecta "camera gear hallucinations"
        # Modelo fica falando sobre câmeras/lentes em vez de iluminação
        gear_patterns = [
            r"\bcanon\b",
            r"\bnikon\b",
            r"\bsony\b",
            r"\bfujifilm\b",
            r"\bpentax\b",
            r"\b5d\b",
            r"\b6d\b",
            r"\b7d\b",
            r"\bmark\s*(ii|iii|iv|i)\b",
            r"\b\d{2,3}mm\b",
            r"\bf\s*/?\s*\d",
            r"\bi have a\b",
            r"\bwith the same issue\b",
            r"\bwith 35mm\b",
            r"\bwith\s+an?\s+(35mm|50mm|24mm|85mm)\b",
            r"\faperture\b",
            r"\blens\b.*\b(macro|prime|zoom)\b",
        ]
        
        lowered = text.lower()
        for pattern in gear_patterns:
            if re.search(pattern, lowered):
                logger.warning(f"Detected camera-gear hallucination in response: {text[:80]}...")
                return None
        
        return text if text else None
    
    #---------------------------------------------------------------------
    def _call_model(self, prompt: str, max_new_tokens: int = None) -> str:
        """
        Chama DialoGPT-small para gerar explicação (single prompt)
        Com validação forte contra junk responses
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
                    repetition_penalty=1.08,
                    no_repeat_ngram_size=3,
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
            
            # Validação: resposta muito curta indica falha
            if not response or len(response.strip()) < 8:
                logger.warning("Short response from model, returning empty")
                return ""
            
            # Pós-processamento + validação de junk
            cleaned = self._postprocess_dialogpt_text(response)
            if cleaned is None:
                logger.warning("Response rejected as junk, returning empty")
                return ""
            
            return self._clean_response(cleaned)
            
        except Exception as e:
            logger.error(f"Error in _call_model: {e}")
            raise
    
    #---------------------------------------------------------------------
    def _call_model_batch(self, prompts: List[str]) -> List[str]:
        """
        Processa múltiplos prompts em batch (TRUE BATCH INFERENCE)
        Com validação forte contra junk responses
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
                    repetition_penalty=1.08,
                    no_repeat_ngram_size=3,
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
                
                # Validação: resposta muito curta
                if not response or len(response.strip()) < 8:
                    responses.append("")
                    continue
                
                # Pós-processamento + validação de junk
                cleaned = self._postprocess_dialogpt_text(response)
                if cleaned is None:
                    responses.append("")
                    continue
                
                responses.append(self._clean_response(cleaned))
            
            t5 = time.time()
            logger.debug(f"Batch decoding: {(t5-t4)*1000:.1f}ms")
            
            return responses
            
        except Exception as e:
            logger.error(f"Error in _call_model_batch: {e}")
            raise
