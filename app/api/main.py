"""
AR Diagnostic MVP - Main API Entry Point
Illumination-only pipeline for Jetson deployment
"""

import logging
import time
import uvicorn
import numpy as np

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from PIL import Image

from app.config.config import Config
from app.api.routes import router, set_pipeline
from app.pipeline.illumination_pipeline import IlluminationPipeline

try:
    from contextlib import asynccontextmanager
except ImportError:
    asynccontextmanager = None

# ------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# Configurar logger para toda a aplicação, garantindo que todas as mensagens de log sejam formatadas de maneira consistente
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)  # Logger específico para este módulo

# ------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# variável global para armazenar a instância do pipeline, permitindo que seja acessada em todo o sistema após ser inicializada durante a startup
pipeline = None


async def initialize_pipeline() -> None:
    """Inicializa o pipeline de diagnóstico e realiza warm-up opcional."""
    global pipeline

    logger.info("Starting AR Diagnostic MVP API...")

    config = Config()
    model_type = config.get("models.default", "qwen")
    use_4bit = config.get("models.use_4bit", True)
    device = config.get("models.device", "cuda")
    warmup_on_startup = config.get("models.warmup_on_startup", True)

    logger.info(
        f"Loading pipeline (model: {model_type}, 4-bit: {use_4bit}, device: {device})"
    )

    pipeline = IlluminationPipeline(
        model_type=model_type,
        use_4bit=use_4bit,
        device=device,
    )

    if warmup_on_startup:
        logger.info("Starting warm-up (1 run)...")

        warmup_start = time.time()

        dummy_image = Image.fromarray(
            np.full((256, 256, 3), 128, dtype=np.uint8)
        )

        t0 = time.time()
        pdi_metrics = pipeline.extract_metrics_batch([dummy_image])
        _, _ = pipeline.diagnose_from_metrics_batch_with_summary(pdi_metrics)

        logger.info(f"   Warmup #1/1: {time.time() - t0:.2f}s")

        warmup_time = time.time() - warmup_start
        logger.info(
            f"✅ Warm-up complete! Model loaded and ready (took {warmup_time:.1f}s)"
        )

    set_pipeline(pipeline)
    logger.info("✅ API ready to accept requests!")


async def shutdown_pipeline() -> None:
    """Finaliza o pipeline de forma ordenada."""
    global pipeline
    logger.info("Shutting down API...")
    pipeline = None


# ------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# Compatibilidade:
# - Python 3.7+ usa lifespan com asynccontextmanager
# - Python 3.6 usa eventos startup/shutdown
if asynccontextmanager is not None:

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        """Application lifespan manager."""
        try:
            await initialize_pipeline()
            yield
        except Exception as e:
            logger.error(f"Error starting API: {e}")
            raise
        finally:
            await shutdown_pipeline()


# ------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# método para criar a instância da aplicação FastAPI, configurando lifespan/eventos, middleware e rotas
def create_app() -> FastAPI:
    """Cria e configura a aplicação FastAPI."""
    if asynccontextmanager is not None:
        app = FastAPI(
            title="AR Diagnostic MVP",
            description="Illumination quality analysis for AR scenes on Jetson",
            version="0.1.0",
            lifespan=lifespan,
        )
    else:
        app = FastAPI(
            title="AR Diagnostic MVP",
            description="Illumination quality analysis for AR scenes on Jetson",
            version="0.1.0",
        )

        @app.on_event("startup")
        async def startup_event():
            try:
                await initialize_pipeline()
            except Exception as e:
                logger.error(f"Error starting API: {e}")
                raise

        @app.on_event("shutdown")
        async def shutdown_event():
            await shutdown_pipeline()

    # CORS middleware: permite que a API seja acessada de qualquer origem
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(router)
    return app


# ------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# Instância global da aplicação FastAPI
app = create_app()


# ------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# método para rodar o servidor API usando Uvicorn
def run():
    """Run the API server."""
    uvicorn.run(
        "app.api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
    )


# ------------------------------------------------------------------------------------------------------------------------------------------------------------------------
if __name__ == "__main__":
    run()
