"""
Model Loader with Fallback Support - Jetson Nano
Tries to load preferred model, falls back to simpler alternatives if needed
"""

import logging
from typing import Optional, Literal

logger = logging.getLogger(__name__)


def load_model_with_fallback(
    preferred_model: Literal['qwen', 'phi', 'gpt2', 'distilbert'] = 'qwen',
    use_4bit: bool = False,
    device: str = 'cpu'
):
    """
    Load model with intelligent fallback chain.
    
    Priority on Jetson Nano (Python 3.6 + transformers 4.8.2 + CPU):
    1. Try preferred model (qwen by default)
    2. Fallback to phi
    3. Fallback to GPT2 (lightweight, always works)
    
    Args:
        preferred_model: Primary model to try ('qwen', 'phi', 'gpt2', 'distilbert')
        use_4bit: Use 4-bit quantization (ignored for fallbacks on Jetson)
        device: Device to load on ('cuda', 'cpu')
    
    Returns:
        Loaded model instance
        
    Raises:
        RuntimeError: If all models fail to load
    """
    
    # Define fallback chain for Jetson Nano
    model_chain = [preferred_model]
    
    if preferred_model != 'qwen':
        model_chain.insert(0, 'qwen')  # Always try qwen first
    if 'phi' not in model_chain:
        model_chain.append('phi')
    if 'gpt2' not in model_chain:
        model_chain.append('gpt2')
    
    logger.info(f"Model loading chain: {' → '.join(model_chain)}")
    
    # Try each model in sequence
    for model_name in model_chain:
        try:
            logger.info(f"Attempting to load {model_name}...")
            
            if model_name == 'qwen':
                from app.models.qwen_model import QwenARModel
                model = QwenARModel(use_4bit=use_4bit, device=device)
                logger.info(f"✅ Loaded Qwen model successfully!")
                return model
                
            elif model_name == 'phi':
                from app.models.phi_model import PhiARModel
                model = PhiARModel(use_4bit=use_4bit, device=device)
                logger.info(f"✅ Loaded Phi model successfully!")
                return model
                
            elif model_name == 'gpt2':
                from app.models.gpt2_model import GPT2ARModel
                model = GPT2ARModel(use_4bit=False, device=device)  # GPT2 doesn't support 4bit
                logger.info(f"✅ Loaded GPT2 model successfully (lightweight fallback)!")
                return model
                
            elif model_name == 'distilbert':
                from app.models.distilbert_model import DistilBERTARModel
                model = DistilBERTARModel(use_4bit=False, device=device)
                logger.info(f"✅ Loaded DistilBERT model successfully!")
                return model
                
        except Exception as e:
            logger.warning(
                f"Failed to load {model_name}: {type(e).__name__}: {str(e)[:150]}"
            )
            # Continue to next model in chain
            continue
    
    # If we get here, all models failed
    error_msg = (
        f"Unable to load any model from chain: {model_chain}\n"
        f"Last error: {e}\n"
        f"Ensure models are cached in /app/models/cache or have internet access."
    )
    logger.error(error_msg)
    raise RuntimeError(error_msg)


def get_model_status_report() -> str:
    """Generate report of available models for logging/debugging"""
    report = []
    report.append("=" * 70)
    report.append("MODEL AVAILABILITY REPORT")
    report.append("=" * 70)
    
    models_to_check = [
        ('Qwen', 'app.models.qwen_model', 'QwenARModel'),
        ('Phi', 'app.models.phi_model', 'PhiARModel'),
        ('GPT2', 'app.models.gpt2_model', 'GPT2ARModel'),
        ('DistilBERT', 'app.models.distilbert_model', 'DistilBERTARModel'),
    ]
    
    for name, module_path, class_name in models_to_check:
        try:
            module = __import__(module_path, fromlist=[class_name])
            cls = getattr(module, class_name)
            report.append(f"  ✅ {name:15} - {class_name}")
        except Exception as e:
            report.append(f"  ❌ {name:15} - NOT AVAILABLE ({type(e).__name__})")
    
    report.append("=" * 70)
    return "\n".join(report)
