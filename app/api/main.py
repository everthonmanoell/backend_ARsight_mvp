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
import uvicorn

#------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# Configurar logger para toda a aplicação, garantindo que todas as mensagens de log sejam formatadas de maneira consistente
logging.basicConfig(level=logging.INFO,format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

logger = logging.getLogger(__name__) # Logger específico para este módulo

#------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# variável global para armazenar a instância do pipeline, permitindo que seja acessada em todo o sistema após ser inicializada durante o lifespan da aplicação
pipeline = None
#------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# Gerenciador de lifespan da aplicação, responsável por inicializar o pipeline de diagnóstico durante a startup 
# e garantir que ele esteja pronto para processar requests; também lida com o shutdown da aplicação de forma ordenada
@asynccontextmanager
async def lifespan(app: FastAPI): 
    """Application lifespan manager"""
    global pipeline
    
    logger.info("Starting AR Diagnostic MVP API...")
    
    try:
        config = Config()                                                     # Carrega configurações do arquivo YAML, incluindo thresholds e parâmetros do modelo
        model_type = config.get('models.default', 'qwen')                     # Obtém o tipo de modelo a ser usado (qwen ou phi) a partir da configuração
        use_4bit = config.get('models.use_4bit', True)                        # Verifica se a quantização 4-bit deve ser usada
        device = config.get('models.device', 'cuda')                          # Verifica qual dispositivo deve ser usado para inferência (cuda, cpu, ou auto)
        warmup_on_startup = config.get('models.warmup_on_startup', True)      # Verifica se o warm-up do modelo deve ser realizado durante a startup 
        
        logger.info(f"Loading pipeline (model: {model_type}, 4-bit: {use_4bit}, device: {device})")

        # Inicializa o pipeline de diagnóstico com as configurações especificadas
        pipeline = IlluminationPipeline(model_type=model_type, use_4bit=use_4bit, device=device) 
        
        # Warm-up: pré-carrega pesos e estabiliza torch.compile() JIT
        # JIT(Just-In-Time compilation) pode levar mais tempo nas primeiras inferências, especialmente com quantização e modelos grandes;
        # realizar um warm-up durante a startup garante que o modelo esteja pronto para processar requests reais com latência otimizada desde o primeiro request

        if warmup_on_startup:
            logger.info("Starting warm-up (1 run)...\n")

            warmup_start = time.time() # Inicia contagem de tempo para o warm-up, permitindo medir quanto tempo leva para carregar o modelo e realizar a primeira inferência

            # Cria uma imagem dummy cinza médio (256x256) para usar como input durante o warm-up, garantindo que o modelo seja carregado e otimizado para processar imagens reais posteriormente
            dummy_image = Image.fromarray(np.full((256, 256, 3), 128, dtype=np.uint8)) 

            t0 = time.time() # Inicia contagem de tempo para a primeira inferência, permitindo medir o tempo que leva para o modelo ser carregado e otimizado durante o warm-up

            # Extrai métricas de PDI da imagem dummy, forçando o pipeline a carregar o modelo e realizar as operações de pré-processamento necessárias
            pdi_metrics = pipeline.extract_metrics_batch([dummy_image]) 

            # Realiza uma inferência completa usando as métricas extraídas, garantindo que o modelo esteja totalmente carregado e otimizado para processar requests reais posteriormente
            _, _ = pipeline.diagnose_from_metrics_batch_with_summary(pdi_metrics) 

            logger.info(f"   Warmup #1/1: {time.time()-t0:.2f}s")

            # Calcula o tempo total gasto no warm-up, incluindo o tempo para carregar o modelo e realizar a primeira inferência,
            # permitindo avaliar o impacto do warm-up na latência inicial da aplicação
            warmup_time = time.time() - warmup_start 

            logger.info(f"✅ Warm-up complete! Model loaded and ready (took {warmup_time:.1f}s)")

        # Define a instância do pipeline para ser usada nas rotas da API, garantindo que as rotas possam acessar o pipeline para processar requests
        set_pipeline(pipeline) 

        logger.info("✅ API ready to accept requests!")
        
        yield # Aguarda até que a aplicação seja encerrada, permitindo que o pipeline continue processando requests enquanto a aplicação estiver ativa
        
    except Exception as e:
        logger.error(f"Error starting API: {e}")
        raise
    finally:
        logger.info("Shutting down API...")
        pipeline = None

#------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# método para criar a instância da aplicação FastAPI, configurando o lifespan, middleware e rotas
def create_app() -> FastAPI: 
    """Cria e configura a aplicação FastAPI"""
  
    app = FastAPI(
        title="AR Diagnostic MVP",
        description="Illumination quality analysis for AR scenes on Jetson",
        version="0.1.0",
        lifespan=lifespan
    )
    
    # CORS middleware: permite que a API seja acessada de qualquer origem, facilitando o desenvolvimento e testes com clientes web ou outras aplicações;
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Incluir as rotas definidas no módulo routes.py
    app.include_router(router)
    
    return app

#------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# Instância global da aplicação FastAPI
app = create_app()

#------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# método para rodar o servidor API usando Uvicorn, permitindo que a aplicação seja executada como um serviço web e possa processar requests de clientes
def run(): 
    """Run the API server"""
    
    uvicorn.run(
        "app.api.main:app",
        host="0.0.0.0", 
        port=8000,
        reload=False  # ← Otimizado para Jetson: CUDA funciona sem reload
    )

#------------------------------------------------------------------------------------------------------------------------------------------------------------------------
if __name__ == "__main__":
    run()
