"""
AR Diagnostic MVP - Main API Entry Point
Illumination-only pipeline for Jetson deployment
"""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config.config import Config
from app.api.routes import router, set_pipeline
from app.pipeline.illumination_pipeline import IlluminationPipeline
import numpy as np
from PIL import Image
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global pipeline instance
pipeline = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    global pipeline
    
    logger.info("Starting AR Diagnostic MVP API...")
    
    try:
        config = Config()
        model_type = config.get('models.default', 'qwen')
        use_4bit = config.get('models.use_4bit', True)
        device = config.get('models.device', 'cuda')
        warmup_on_startup = config.get('models.warmup_on_startup', True)
        
        logger.info(f"Loading pipeline (model: {model_type}, 4-bit: {use_4bit}, device: {device})")
        
        pipeline = IlluminationPipeline(
            model_type=model_type,
            use_4bit=use_4bit,
            device=device
        )
        
        # Warm-up: pré-carrega pesos e estabiliza torch.compile() JIT
        if warmup_on_startup:
            # torch.compile recompila nas primeiras N chamadas (tracing JIT);
            # 3 runs com brightness variado garantem que o modelo está estável
            # antes de aceitar requests reais.
            warmup_runs = 3 if enable_compile else 1
            logger.info(f"🔥 Starting warm-up ({warmup_runs} run(s), compile={enable_compile})...")
            warmup_start = time.time()

            brightness_levels = [80, 128, 200]  # escuro / normal / claro
            for i in range(warmup_runs):
                dummy_image = Image.fromarray(
                    np.full((256, 256, 3), brightness_levels[i % len(brightness_levels)], dtype=np.uint8)
                )
                t0 = time.time()
                _ = pipeline.diagnose(dummy_image)
                logger.info(f"   Warmup #{i+1}/{warmup_runs}: {time.time()-t0:.2f}s")

            warmup_time = time.time() - warmup_start

            if enable_compile:
                logger.info(f"✅ Warm-up complete! Model compiled and stable (took {warmup_time:.1f}s)")
            else:
                logger.info(f"✅ Warm-up complete! Model loaded and ready (took {warmup_time:.1f}s)")
        
        set_pipeline(pipeline)
        logger.info("🚀 API ready to accept requests!")
        
        yield
        
    except Exception as e:
        logger.error(f"Error starting API: {e}")
        raise
    finally:
        logger.info("Shutting down API...")
        pipeline = None


def create_app() -> FastAPI:
    """Create FastAPI application"""
    app = FastAPI(
        title="AR Diagnostic MVP",
        description="Illumination quality analysis for AR scenes on Jetson",
        version="0.1.0",
        lifespan=lifespan
    )
    
    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Include routes
    app.include_router(router)
    
    return app


# Create app instance
app = create_app()


def run():
    """Run the API server"""
    import uvicorn
    uvicorn.run(
        "app.api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )


if __name__ == "__main__":
    run()
