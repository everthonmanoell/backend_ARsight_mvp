"""
API Routes for AR Diagnostic MVP
Illumination-only endpoints
"""

import logging
import os
from typing import List, Optional
from datetime import datetime
import time as _time
from fastapi import APIRouter, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
from PIL import Image
import io

from app.pipeline.illumination_pipeline import IlluminationPipeline
from app.config.config import Config

# configura logger para este módulo
logger = logging.getLogger(__name__)


#----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# router específico para endpoints de diagnóstico
router = APIRouter() 

# Variável global para armazenar a instância do pipeline, que será configurada no startup da API e acessada pelos endpoints para realizar diagnósticos
_pipeline: Optional[IlluminationPipeline] = None 


# método para configurar a instância global do pipeline, chamada durante o startup da API - setter para a variável global _pipeline
def set_pipeline(pipeline: IlluminationPipeline): 
    """Set global pipeline instance"""
    global _pipeline
    _pipeline = pipeline


# método para acessar a instância global do pipeline, garantindo que ele foi inicializado antes de ser usado - getter para a variável global _pipeline
def get_pipeline() -> IlluminationPipeline: 
    """Get global pipeline instance"""
    if _pipeline is None:
        raise HTTPException(status_code=503, detail="Pipeline not initialized")
    return _pipeline

#----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# método auxiliar para validar e carregar uma imagem a partir do arquivo enviado, garantindo que o formato e tamanho são adequados antes de processar a imagem
def _validate_image_file(file: UploadFile) -> Image.Image:
    """
    Valida e carrega a imagem enviada
    
    Args:
        file: arquivo enviado (UploadFile)
    
    Returns:
        PIL Image
        
    Raises:
        HTTPException: se o arquivo for inválido
    """
    config = Config()
    allowed_formats: list = config.get('api.allowed_formats', ['jpg', 'jpeg', 'png', 'bmp'])
    max_size: int         = config.get('api.max_image_size', 10 * 1024 * 1024)

    # Checar se o formato do arquivo é permitido (baseado na extensão)
    # se não for, lança uma exceção HTTP 400 indicando que o formato é inválido
    file_ext = file.filename.split('.')[-1].lower()
    if file_ext not in allowed_formats:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid file format. Allowed: {', '.join(allowed_formats)}"
        )
    
    # Ler e validar o conteúdo do arquivo, tentando abrir como imagem usando PIL; 
    # se falhar, lança uma exceção HTTP 400 indicando que o arquivo é inválido
    try:
        contents = file.file.read()
        image = Image.open(io.BytesIO(contents))
        
        if len(contents) > max_size:
            raise HTTPException(
                status_code=400,
                detail=f"File too large. Max size: {max_size / 1024 / 1024:.0f}MB"
            )
        
        return image

    # Em caso de qualquer erro durante a leitura ou validação da imagem, captura a exceção 
    # e lança uma HTTPException com status 400 e detalhes do erro   
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid image file: {str(e)}")
    finally:
        file.file.seek(0)

#----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# Root endpoint, fornece informações básicas sobre a API e seus endpoints disponíveis
@router.get("/") 
async def root():
    return {
        "message": "AR Diagnostic MVP - Illumination Analysis",
        "version": "0.1.0",
        "endpoints": {
            "health":         "GET  /health          — status da API e modelo carregado",
            "diagnose_batch": "POST /diagnose/batch  — diagnóstico de 1-10 imagens (PDI + SLM)",
            "upload_batch":   "POST /upload/batch    — salva imagens em disco",
            "docs":           "GET  /docs            — documentação interativa (Swagger)"
        }
    }

#----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# endpoint para verificar se a API está saudável, retornando status e informações sobre o modelo carregado
@router.get("/health")
async def health():
    """Health check endpoint"""
    try:
        # tenta acessar a instância do pipeline para verificar se está inicializada e funcional
        pipeline = get_pipeline() 

        # retorna um dicionário indicando que a API está saudável, junto com informações sobre o modelo carregado (tipo, dispositivo, quantização)
        return {
            "status": "healthy",
            "model": pipeline.model_type,
            "device": pipeline.device,
            "quantization": "4-bit" if pipeline.use_4bit else "fp16/fp32"
        }
    
    # caso ocorra qualquer exceção (como pipeline não inicializado), captura a exceção e retorna um JSON indicando que a API está com problemas
    except Exception as e:
        return JSONResponse(
            status_code=503,
            content={"status": "unhealthy", "error": str(e)} # inclui detalhes do erro
        )

#----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# endpoint principal para diagnóstico em batch, recebe uma lista de arquivos de imagem, processa cada um e retorna um resumo geral mais detalhes por frame
@router.post("/diagnose/batch") 
async def diagnose_batch(files: List[UploadFile] = File(...)):
    """
    Diagnosticar um lote de imagens, retornando um resumo geral e detalhes por frame.

    Retorna um `summary` do ambiente geral e uma lista `frames` com resultados por quadro.
    O summary é gerado pelo SLM usando estatísticas agregadas de PDI (N+1 prompts
    em um único forward pass em batch — sem custo adicional de latência).

    Args:
        files: Lista de arquivos de imagem (1-10)

    Returns:
        {
          "summary": { overall_risk, dominant_label, problem_count, normal_count,
                       explanation, recommendations, metrics_avg, processing_time_s },
          "frames":  [ { frame_index, filename, risk_level, status, explanation,
                         triggered_rules, recommendations, metrics, status_code } ]
        }
    """
    

    try:
        # valida o número de arquivos enviados, garantindo que não exceda o limite configurado (default 10) 
        # e que haja pelo menos um arquivo; caso contrário, lança uma HTTPException com status 400 e detalhes do erro
        max_batch_size: int = Config().get('api.max_batch_size', 10)

        if len(files) > max_batch_size:
            raise HTTPException(
                status_code=400,
                detail=f"Too many files. Max batch size: {max_batch_size}"
            )
        if len(files) == 0:
            raise HTTPException(status_code=400, detail="No files provided")

        # acessa a instância global do pipeline para realizar o diagnóstico
        pipeline = get_pipeline() 

        # 1. Valida e carrega imagens 
        # lista valid_items armazena tuplas de (índice original, nome do arquivo, imagem PIL) para os arquivos que foram validados com sucesso
        valid_items: list = [] 

        # lista error_frames armazena dicionários com detalhes dos arquivos que falharam na validação, incluindo índice, nome do arquivo, código de status HTTP e mensagem de erro
        error_frames: list = []

        # iterar sobre os arquivos enviados, validando cada um usando a função _validate_image_file
        for i, file in enumerate(files):
            try:
                image = _validate_image_file(file)
                valid_items.append((i, file.filename, image))

            # captura especificamente HTTPException para erros de validação de imagem, registrando o erro e adicionando um dicionário ao error_frames com detalhes do erro
            except HTTPException as e: 
                logger.error(f"Validation error for {file.filename}: {e.detail}")
                error_frames.append({
                    'frame_index': i,
                    'filename':    file.filename,
                    'status_code': e.status_code,
                    'error':       e.detail
                })
            # captura qualquer outra exceção inesperada durante a validação
            except Exception as e: 
                logger.error(f"Error loading {file.filename}: {e}")
                error_frames.append({
                    'frame_index': i,
                    'filename':    file.filename,
                    'status_code': 500,
                    'error':       str(e)
                })

        # lista success_frames armazena dicionários com detalhes dos arquivos que foram processados com sucesso
        success_frames: list = [] 

        # dicionário summary armazena informações agregadas sobre o ambiente geral
        summary: dict = {} 

        t_start = _time.time() # registra o tempo de início do processamento para calcular o tempo total gasto no diagnóstico

        # verifica se há itens válidos para processar; se houver, extrai os índices, nomes dos arquivos e imagens correspondentes para realizar o diagnóstico em batch usando o pipeline
        if valid_items:
            indices   = [idx for idx, _, _ in valid_items]
            filenames = [fn  for _, fn, _ in valid_items]
            images    = [img for _, _, img in valid_items]

            try:
                # 2. PDI batch 

                # extrai métricas de para todas as imagens em um único batch, retornando uma lista de dicionários de métricas correspondentes a cada imagem
                pdi_metrics = pipeline.extract_metrics_batch(images) 

                # 3. SLM batch (N+1 prompts: N individuais + 1 summary)

                # realiza o diagnóstico para todas as imagens em um único batch, retornando uma lista de diagnósticos individuais e um resumo geral do ambiente
                diagnoses, summary = pipeline.diagnose_from_metrics_batch_with_summary(pdi_metrics) 

                # itera sobre os resultados dos diagnósticos individuais, associando cada diagnóstico ao índice original e nome do arquivo correspondente, 
                # e adicionando detalhes do diagnóstico e métricas ao dicionário resultante, que é adicionado à lista success_frames
                for orig_idx, filename, pdi, result in zip(indices, filenames, pdi_metrics, diagnoses):
                    result['frame_index'] = orig_idx
                    result['filename']    = filename
                    result['status_code'] = 200
                    result['metrics'] = {
                        'illumination_score': round(pdi.get('illumination', 0.0), 4),
                        'illumination_label': pdi.get('illumination_label', 'unknown'),
                        'mean_brightness':    round(pdi.get('mean_luma', 0.0) / 255.0, 4),
                        'mean_luma':          round(pdi.get('mean_luma', 0.0), 2),
                        'std_luma':           round(pdi.get('std_luma', 0.0), 2),
                        'uniformity':         round(pdi.get('uniformity', 0.0), 4),
                        'pct_clipped_dark':   round(pdi.get('pct_clipped_dark', 0.0), 4),
                        'pct_clipped_bright': round(pdi.get('pct_clipped_bright', 0.0), 4),
                    }
                    success_frames.append(result)

            # se ocorrer qualquer erro durante o processamento em batch (como falha na extração de métricas ou diagnóstico), captura a exceção e registra o erro, 
            # tentando realizar um fallback para processar cada imagem individualmente
            except Exception as e: 

                logger.error(f"Batch+summary inference failed, falling back to sequential batch: {e}")

                try:
                    fb_images  = [img  for _, _, img  in valid_items]
                    fb_indices = [idx  for idx, _, _  in valid_items]
                    fb_names   = [name for _, name, _ in valid_items]
                    fb_metrics = pipeline.extract_metrics_batch(fb_images)
                    fb_diagnoses, summary = pipeline.diagnose_from_metrics_batch_with_summary(fb_metrics)
                    for orig_idx, filename, result in zip(fb_indices, fb_names, fb_diagnoses):
                        result['frame_index'] = orig_idx
                        result['filename']    = filename
                        result['status_code'] = 200
                        success_frames.append(result)
                except Exception as e2: 
                    logger.error(f"Sequential fallback also failed: {e2}")
                    for orig_idx, filename, _ in valid_items:
                        error_frames.append({
                            'frame_index': orig_idx,
                            'filename':    filename,
                            'status_code': 500,
                            'error':       str(e2)
                        })
                    summary = {
                        'overall_risk':   'unknown',
                        'dominant_label': 'unknown',
                        'problem_count':  0,
                        'normal_count':   0,
                        'explanation':    'Summary unavailable due to inference error.',
                        'recommendations': [],
                        'metrics_avg':    {}
                    }

        # calcula o tempo total gasto no processamento do lote, desde a validação das imagens até a geração dos diagnósticos e resumo, 
        # e adiciona essa informação ao dicionário summary para fornecer contexto sobre a latência da API ao processar o lote de imagens
        processing_time_s = round(_time.time() - t_start, 3) 
        summary['processing_time_s'] = processing_time_s

        # Frames ordenados pelo índice original
        all_frames = sorted(success_frames + error_frames, key=lambda f: f.get('frame_index', 0))

        return {
            'summary': summary,
            'frames':  all_frames
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing batch: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing batch: {str(e)}")

#----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# endpoint para upload e salvamento de múltiplas imagens em disco, com validação de formato e tamanho, e retorno de informações sobre os arquivos processados
@router.post("/upload/batch") 
async def upload_batch(files: List[UploadFile] = File(...)):
    """
    Upload and save multiple images to disk
    
    Args:
        files: List of image files (max 10)
        
    Returns:
        List of saved file info
    """

    # valida o número de arquivos enviados, garantindo que não exceda o limite configurado (default 10) e que haja pelo menos um arquivo; 
    # caso contrário, lança uma HTTPException com status 400 e detalhes do erro
    try:
        max_batch_size: int = Config().get('api.max_batch_size', 10)
        if len(files) > max_batch_size:
            raise HTTPException(
                status_code=400,
                detail=f"Too many files. Max batch size: {max_batch_size}"
            )
        
        if len(files) == 0:
            raise HTTPException(status_code=400, detail="No files provided")
        
        # acessa as configurações para determinar o diretório onde os arquivos serão salvos, criando o diretório se ele não existir
        config = Config()
        upload_dir = config.get('api.upload_dir', 'data/uploads')
        
        # Criar diretório de upload se não existir
        os.makedirs(upload_dir, exist_ok=True)
        
        # lista para armazenar os resultados do processamento de cada arquivo, incluindo informações sobre o nome original, nome salvo, caminho, tamanho e status do processamento
        results = []

        # gera um timestamp para criar nomes de arquivos únicos, evitando sobrescritas e facilitando a organização dos arquivos salvos
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # itera sobre os arquivos enviados, validando cada um usando a função _validate_image_file e salvando a imagem no diretório especificado; 
        # para cada arquivo, gera um nome de arquivo único usando o timestamp e o nome original
        for i, file in enumerate(files):
            try:
                # Valida arquivo
                image = _validate_image_file(file)
                
                # Gera nome de arquivo único e caminho para salvar a imagem
                saved_filename = f"{timestamp}_{i:02d}_{file.filename}"
                saved_path = os.path.join(upload_dir, saved_filename)
                
                # Salva imagem
                image.save(saved_path)
                
                results.append({
                    'filename': file.filename,
                    'saved_as': saved_filename,
                    'path': saved_path,
                    'size_bytes': os.path.getsize(saved_path),
                    'image_size': f"{image.width}x{image.height}",
                    'status': 'success'
                })
                
            except HTTPException as e:
                results.append({
                    'filename': file.filename,
                    'status': 'error',
                    'error': e.detail
                })
            except Exception as e:
                logger.error(f"Error uploading {file.filename}: {e}")
                results.append({
                    'filename': file.filename,
                    'status': 'error',
                    'error': str(e)
                })
        
        # retorna um resumo do processamento, incluindo o número total de arquivos processados, quantos foram salvos com sucesso e quantos apresentaram erros, junto com os detalhes de cada arquivo processado
        return {
            'total': len(files),
            'successful': sum(1 for r in results if r.get('status') == 'success'),
            'failed': sum(1 for r in results if r.get('status') != 'success'),
            'results': results
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading batch: {e}")
        raise HTTPException(status_code=500, detail=f"Error uploading batch: {str(e)}")
