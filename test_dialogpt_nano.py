#!/usr/bin/env python3
"""
Quick test script for DialoGPT-small on Jetson Nano
Tests model loading, inference, and batch processing
"""

import sys
import logging
import time
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)
logger = logging.getLogger(__name__)

# Add app to path
app_path = Path(__file__).parent / 'app'
sys.path.insert(0, str(Path(__file__).parent))

def test_model_loading():
    """Test 1: Load DialoGPT-small model"""
    logger.info("=" * 80)
    logger.info("TEST 1: Model Loading")
    logger.info("=" * 80)
    
    try:
        from app.models.dialogpt_model import DialoGPTARModel
        
        logger.info("Importing DialoGPTARModel...")
        model = DialoGPTARModel(use_4bit=False, device='cuda')
        logger.info(f"✅ Model loaded successfully on device: {model.device}")
        logger.info(f"   Model name: {model.model_name}")
        logger.info(f"   Max tokens: {model.max_tokens}")
        logger.info(f"   Greedy decoding: {model.greedy_decoding}")
        
        return model
        
    except Exception as e:
        logger.error(f"❌ Failed to load model: {e}", exc_info=True)
        return None

def test_single_inference(model):
    """Test 2: Single inference"""
    logger.info("\n" + "=" * 80)
    logger.info("TEST 2: Single Inference")
    logger.info("=" * 80)
    
    try:
        # Build a test prompt using the model's method
        test_metrics = {
            'illumination_label': 'normal',
            'illumination': 0.8,
            'mean_luma': 128,
            'uniformity': 0.75
        }
        
        prompt = model._build_prompt(
            metrics=test_metrics,
            status='pass',
            risk_level='low',
            triggered_rules=[]
        )
        
        logger.info(f"Test prompt:\n{prompt[:100]}...")
        
        t0 = time.time()
        response = model._call_model(prompt, max_new_tokens=40)
        elapsed = time.time() - t0
        
        logger.info(f"✅ Single inference completed in {elapsed:.2f}s")
        logger.info(f"   Response: {response[:100]}...")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Single inference failed: {e}", exc_info=True)
        return False

def test_batch_inference(model):
    """Test 3: Batch inference"""
    logger.info("\n" + "=" * 80)
    logger.info("TEST 3: Batch Inference")
    logger.info("=" * 80)
    
    try:
        # Create 3 test prompts
        test_prompts = [
            "Scene lighting: bright conditions detected. Brightness 200/255. Good uniformity. Suitable for AR.",
            "Lighting diagnostic: dark lighting observed. Brightness 50/255. Uneven. Affects AR performance.",
            "Analysis: normal lighting throughout. Brightness 128/255. Optimal for tracking."
        ]
        
        logger.info(f"Batch processing {len(test_prompts)} prompts...")
        
        t0 = time.time()
        responses = model._call_model_batch(test_prompts)
        elapsed = time.time() - t0
        
        logger.info(f"✅ Batch inference completed in {elapsed:.2f}s")
        logger.info(f"   Average time per prompt: {elapsed/len(test_prompts):.2f}s")
        
        for i, resp in enumerate(responses, 1):
            logger.info(f"   [{i}] {resp[:80]}...")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Batch inference failed: {e}", exc_info=True)
        return False

def test_summary_prompt(model):
    """Test 4: Summary prompt generation"""
    logger.info("\n" + "=" * 80)
    logger.info("TEST 4: Summary Prompt Generation")
    logger.info("=" * 80)
    
    try:
        # Test aggregation data
        agg = {
            'total': 10,
            'problem_count': 3,
            'dominant_label': 'overexposed'
        }
        
        prompt = model._build_summary_prompt(agg)
        logger.info(f"Summary prompt:\n{prompt}")
        
        # Now call model with it
        t0 = time.time()
        response = model._call_model(prompt, max_new_tokens=60)
        elapsed = time.time() - t0
        
        logger.info(f"✅ Summary inference completed in {elapsed:.2f}s")
        logger.info(f"   Response: {response}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Summary test failed: {e}", exc_info=True)
        return False

def test_vram_usage(model):
    """Test 5: VRAM usage inspection"""
    logger.info("\n" + "=" * 80)
    logger.info("TEST 5: VRAM Usage")
    logger.info("=" * 80)
    
    try:
        import torch
        
        if model.device == 'cuda':
            allocated = torch.cuda.memory_allocated() / 1e9
            reserved = torch.cuda.memory_reserved() / 1e9
            total = torch.cuda.get_device_properties(0).total_memory / 1e9
            
            logger.info(f"✅ VRAM Status:")
            logger.info(f"   Allocated: {allocated:.2f} GB")
            logger.info(f"   Reserved:  {reserved:.2f} GB")
            logger.info(f"   Total:     {total:.2f} GB")
            logger.info(f"   Free:      {total - reserved:.2f} GB")
            
            if allocated < total * 0.5:
                logger.info(f"   ✅ VRAM usage is healthy (< 50%)")
            else:
                logger.warning(f"   ⚠️  VRAM usage is high (> 50%)")
        else:
            logger.info(f"Model on CPU, skipping VRAM check")
        
        return True
        
    except Exception as e:
        logger.error(f"⚠️  VRAM check skipped: {e}")
        return True  # Not critical

def main():
    """Run all tests"""
    logger.info("\n")
    logger.info("╔" + "=" * 78 + "╗")
    logger.info("║" + " " * 78 + "║")
    logger.info("║" + "DialoGPT-small Model Test Suite (Jetson Nano)".center(78) + "║")
    logger.info("║" + " " * 78 + "║")
    logger.info("╚" + "=" * 78 + "╝")
    
    # Test 1: Model loading
    model = test_model_loading()
    if not model:
        logger.error("Cannot continue without model")
        return False
    
    # Test 2: Single inference
    test1 = test_single_inference(model)
    
    # Test 3: Batch inference
    test2 = test_batch_inference(model)
    
    # Test 4: Summary prompt
    test3 = test_summary_prompt(model)
    
    # Test 5: VRAM usage
    test4 = test_vram_usage(model)
    
    # Summary
    logger.info("\n" + "=" * 80)
    logger.info("TEST SUMMARY")
    logger.info("=" * 80)
    
    results = {
        'Single Inference': test1,
        'Batch Inference': test2,
        'Summary Prompt': test3,
        'VRAM Check': test4
    }
    
    all_passed = all(results.values())
    
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        logger.info(f"{test_name}: {status}")
    
    logger.info("=" * 80)
    
    if all_passed:
        logger.info("✅ ALL TESTS PASSED")
        return True
    else:
        logger.error("❌ SOME TESTS FAILED")
        return False

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
