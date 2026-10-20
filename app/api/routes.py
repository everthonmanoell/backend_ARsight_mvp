"""
API Routes for AR Diagnostic MVP
Illumination-only endpoints
"""

import logging
import os
import json
import hashlib
from typing import List, Optional
from datetime import datetime
import time as _time
from fastapi import APIRouter, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
from PIL import Image, ImageOps
import io

from app.pipeline.illumination_pipeline import IlluminationPipeline
from app.config.config import Config

# configura logger para este módulo
logger = logging.getLogger(__name__)

#----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# BATCH MANAGEMENT HELPERS
#----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

def _generate_batch_id() -> str:
    """Gera um ID único para batch no formato: batch_YYYYMMDDhhmmss_hash"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    hash_suffix = hashlib.md5(f"{timestamp}{_time.time()}".encode()).hexdigest()[:6]
    return f"batch_{timestamp}_{hash_suffix}"


def _get_environment() -> str:
    """Retorna o environment detectando pela máquina ou YAML"""
    import socket
    import os
    
    # Opção 1: Usar variável de ambiente (se setada)
    env_var = os.environ.get('AR_ENVIRONMENT')
    if env_var:
        return env_var.lower()
    
    # Opção 2: Usar YAML config se disponível  
    try:
        config = Config()
        env_from_yaml = config.get('environment', None)
        if env_from_yaml and env_from_yaml.lower() not in ['unknown', 'auto']:
            if env_from_yaml.lower() == 'jetson':
                # Se é "jetson" no YAML, detectar qual tipo
                return _detect_jetson_type()
            return env_from_yaml.lower()
    except:
        pass
    
    # Opção 3: Detectar pelo hostname (mais confiável)
    try:
        hostname = socket.gethostname().lower()
        logger.info(f"DEBUG: hostname = {hostname}")
        if 'nano' in hostname:
            return 'jetson-nano'
        elif 'orin' in hostname:
            return 'jetson-orin'
        elif 'legion' in hostname or 'pc062' in hostname:
            return 'desktop-legion'
        elif 'farmacia' in hostname:
            return 'jetson-orin'  # farmaciaback = Orin
    except Exception as e:
        logger.warning(f"DEBUG: Error detecting hostname: {e}")
    
    # Opção 4: Detectar pela GPU
    return _detect_jetson_type()


def _detect_jetson_type() -> str:
    """Detecta tipo de Jetson ou desktop pela GPU"""
    try:
        import torch
        if not torch.cuda.is_available():
            return 'cpu'
        
        device_name = torch.cuda.get_device_name(0).lower()
        logger.info(f"DEBUG: GPU device_name = {device_name}")
        
        if 'orin' in device_name:
            return 'jetson-orin'
        elif 'nano' in device_name or 'tegra' in device_name or 'maxwell' in device_name:
            return 'jetson-nano'
        elif 'rtx' in device_name or 'quadro' in device_name or 'tesla' in device_name:
            return 'desktop-rtx'
        else:
            return 'desktop-gpu'
    except Exception as e:
        logger.error(f"DEBUG: Error detecting GPU: {e}")
        return 'unknown'


def _get_batch_dir(batch_id: str) -> str:
    """Retorna o caminho da pasta do batch"""
    config = Config()
    upload_base_dir = config.get('api.upload_dir', 'data/uploads')
    return os.path.join(upload_base_dir, batch_id)


def _get_batch_status_file(batch_id: str) -> str:
    """Retorna o caminho do arquivo status.json"""
    return os.path.join(_get_batch_dir(batch_id), 'status.json')


def _get_batch_metadata_file(batch_id: str) -> str:
    """Retorna o caminho do arquivo metadata.json"""
    return os.path.join(_get_batch_dir(batch_id), 'metadata.json')


def _get_batch_result_file(batch_id: str) -> str:
    """Retorna o caminho do arquivo resultado final"""
    config = Config()
    output_dir = config.get('api.output_dir', 'outputs')
    return os.path.join(output_dir, f'{batch_id}_result.json')


def _load_batch_status(batch_id: str) -> dict:
    """Carrega o status do batch"""
    status_file = _get_batch_status_file(batch_id)
    
    if not os.path.exists(status_file):
        return {
            'batch_id': batch_id,
            'status': 'unknown'
        }
    
    try:
        with open(status_file, 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading status for batch {batch_id}: {e}")
        return {
            'batch_id': batch_id,
            'status': 'error',
            'error': str(e)
        }


def _save_batch_status(batch_id: str, status: str, metadata: dict = None) -> dict:
    """Salva o status do batch"""
    batch_dir = _get_batch_dir(batch_id)
    status_file = _get_batch_status_file(batch_id)
    
    os.makedirs(batch_dir, exist_ok=True)
    
    status_data = {
        'batch_id': batch_id,
        'status': status,
        'updated_at': datetime.now().isoformat()
    }
    
    if metadata:
        status_data.update(metadata)
    
    try:
        with open(status_file, 'w') as f:
            json.dump(status_data, f, indent=2)
        return status_data
    except Exception as e:
        logger.error(f"Error saving status for batch {batch_id}: {e}")
        raise


def _save_batch_metadata(batch_id: str, metadata: dict) -> dict:
    """Salva metadata do batch"""
    batch_dir = _get_batch_dir(batch_id)
    metadata_file = _get_batch_metadata_file(batch_id)
    
    os.makedirs(batch_dir, exist_ok=True)
    
    metadata_data = {
        'batch_id': batch_id,
        'created_at': datetime.now().isoformat(),
        **metadata
    }
    
    try:
        with open(metadata_file, 'w') as f:
            json.dump(metadata_data, f, indent=2)
        return metadata_data
    except Exception as e:
        logger.error(f"Error saving metadata for batch {batch_id}: {e}")
        raise


def _save_batch_result(batch_id: str, result: dict) -> str:
    """Salva o resultado do diagnóstico e atualiza status"""
    config = Config()
    output_dir = config.get('api.output_dir', 'outputs')
    result_file = _get_batch_result_file(batch_id)
    
    os.makedirs(output_dir, exist_ok=True)
    
    try:
        with open(result_file, 'w') as f:
            json.dump(result, f, indent=2)
        
        # Atualiza status para completed
        _save_batch_status(batch_id, 'completed', {
            'result_file': result_file,
            'completed_at': datetime.now().isoformat()
        })
        
        logger.info(f"Result saved for batch {batch_id} at {result_file}")
        return result_file
    except Exception as e:
        logger.error(f"Error saving result for batch {batch_id}: {e}")
        _save_batch_status(batch_id, 'failed', {'error': str(e)})
        raise


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
def _process_diagnose_batch_internal(images: List[Image.Image], filenames: List[str], batch_id: str = None) -> dict:
    """
    Função auxiliar para processar diagnóstico de um lote de imagens.
    Retorna JSON completo com metadata, performance, statistics, summary e frames.
    
    Args:
        images: Lista de PIL Images
        filenames: Lista de nomes de arquivo
        batch_id: ID do batch (para metadata)
        
    Returns:
        {
            'metadata': {...},
            'performance': {...},
            'statistics': {...},
            'summary': {...},
            'frames': [...]
        }
    """
    try:
        pipeline = get_pipeline()
        config = Config()
        
        success_frames: list = []
        error_frames: list = []
        summary: dict = {}
        
        # Tempos de processamento
        t_pdi_start = _time.time()
        t_slm_start = None
        pdi_metrics = []
        
        if images:
            try:
                # 1. PDI batch (extração de métricas)
                pdi_metrics = pipeline.extract_metrics_batch(images)
                t_pdi_elapsed = _time.time() - t_pdi_start
                
                # 2. SLM batch (diagnóstico + summary)
                t_slm_start = _time.time()
                diagnoses, summary = pipeline.diagnose_from_metrics_batch_with_summary(pdi_metrics)
                t_slm_elapsed = _time.time() - t_slm_start
                
                # Itera sobre resultados
                for idx, filename, pdi, result in zip(range(len(images)), filenames, pdi_metrics, diagnoses):
                    result['frame_index'] = idx
                    result['filename'] = filename
                    result['status_code'] = 200
                    result['metrics'] = {
                        'illumination_score': round(pdi.get('illumination', 0.0), 4),
                        'illumination_label': pdi.get('illumination_label', 'unknown'),
                        'mean_brightness': round(pdi.get('mean_luma', 0.0) / 255.0, 4),
                        'mean_luma': round(pdi.get('mean_luma', 0.0), 2),
                        'std_luma': round(pdi.get('std_luma', 0.0), 2),
                        'uniformity': round(pdi.get('uniformity', 0.0), 4),
                        'pct_clipped_dark': round(pdi.get('pct_clipped_dark', 0.0), 4),
                        'pct_clipped_bright': round(pdi.get('pct_clipped_bright', 0.0), 4),
                    }
                    success_frames.append(result)
                    
            except Exception as e:
                logger.error(f"Batch+summary inference failed, falling back to sequential batch: {e}")
                t_pdi_elapsed = _time.time() - t_pdi_start
                t_slm_start = _time.time()
                
                try:
                    fb_metrics = pipeline.extract_metrics_batch(images)
                    fb_diagnoses, summary = pipeline.diagnose_from_metrics_batch_with_summary(fb_metrics)
                    t_slm_elapsed = _time.time() - t_slm_start
                    
                    for idx, filename, result in zip(range(len(images)), filenames, fb_diagnoses):
                        result['frame_index'] = idx
                        result['filename'] = filename
                        result['status_code'] = 200
                        success_frames.append(result)
                except Exception as e2:
                    logger.error(f"Sequential fallback also failed: {e2}")
                    t_slm_elapsed = _time.time() - (t_slm_start or t_pdi_start)
                    
                    for idx, filename in zip(range(len(images)), filenames):
                        error_frames.append({
                            'frame_index': idx,
                            'filename': filename,
                            'status_code': 500,
                            'error': str(e2)
                        })
                    summary = {
                        'overall_risk': 'unknown',
                        'dominant_label': 'unknown',
                        'problem_count': 0,
                        'normal_count': 0,
                        'explanation': 'Summary unavailable due to inference error.',
                        'recommendations': [],
                        'metrics_avg': {}
                    }
        
        # Tempos totais
        total_time_s = _time.time() - t_pdi_start
        pdi_total_ms = round(t_pdi_elapsed * 1000, 1)
        slm_total_s = round(t_slm_elapsed, 3) if t_slm_start else 0
        
        # Contar frames corretos para estatísticas
        correct_frames = sum(1 for f in success_frames if f.get('status_code') == 200)
        accuracy = (correct_frames / len(images) * 100) if images else 0
        
        all_frames = sorted(success_frames + error_frames, key=lambda f: f.get('frame_index', 0))
        
        return {
            'metadata': {
                'timestamp': datetime.now().isoformat(),
                'batch_id': batch_id or 'unknown',
                'environment': _get_environment(),
                'model': config.get('models.default', 'qwen'),
                'device': config.get('models.device', 'cuda'),
                'quantization': '4-bit' if config.get('models.use_4bit', False) else 'fp32',
                'batch_size': len(images)
            },
            'performance': {
                'pdi_total_ms': pdi_total_ms,
                'pdi_per_image_ms': round(pdi_total_ms / len(images), 1) if images else 0,
                'slm_total_s': slm_total_s,
                'slm_per_diagnosis_s': round(slm_total_s / len(images), 3) if images else 0,
                'total_s': round(total_time_s, 3),
                'target_met': total_time_s < 5.0  # Target: menos de 5s para 10 imagens
            },
            'statistics': {
                'total': len(images),
                'correct': correct_frames,
                'accuracy': round(accuracy, 1)
            },
            'summary': summary,
            'frames': all_frames
        }
        
    except Exception as e:
        logger.error(f"Error in diagnose batch internal: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing diagnosis: {str(e)}")


def _validate_image_file(file: UploadFile) -> Image.Image:
    """
    Valida e carrega a imagem enviada.
    Mais tolerante com EXIF/metadados problemáticos.
    """
    config = Config()
    allowed_formats: list = config.get("api.allowed_formats", ["jpg", "jpeg", "png", "bmp"])
    max_size: int = config.get("api.max_image_size", 10 * 1024 * 1024)

    file_ext = file.filename.split(".")[-1].lower()
    if file_ext not in allowed_formats:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file format. Allowed: {', '.join(allowed_formats)}"
        )

    try:
        contents = file.file.read()

        if len(contents) > max_size:
            raise HTTPException(
                status_code=400,
                detail=f"File too large. Max size: {max_size / 1024 / 1024:.0f}MB"
            )

        image = Image.open(io.BytesIO(contents))

        # Força leitura real da imagem para detectar corrupção cedo
        image.load()

        # EXIF pode quebrar em alguns arquivos na Nano/Pillow antigo.
        # Tenta rotacionar corretamente; se falhar, segue sem EXIF.
        try:
            image = ImageOps.exif_transpose(image)
        except Exception as exif_err:
            logger.warning(f"EXIF transpose failed for {file.filename}: {exif_err}")

        # Normaliza modo para evitar problemas ao salvar/processar depois
        if image.mode not in ("RGB", "L"):
            image = image.convert("RGB")
        elif image.mode == "L":
            image = image.convert("RGB")

        return image.copy()

    except HTTPException:
        raise
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
#----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# NOVA ARQUITETURA: Diagnóstico em 2 etapas (upload + processing)
#
# POST /upload/batch          → salva imagens, retorna batch_id
# POST /diagnose/batch/{id}   → inicia/processa diagnóstico
# GET  /diagnose/batch/{id}/status → consulta status
# GET  /diagnose/batch/{id}/result → busca resultado
#----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

@router.post("/diagnose/batch/{batch_id}") 
async def diagnose_batch_start(batch_id: str):
    """
    Inicia o diagnóstico de um batch já salvo.
    
    Se já terminou, retorna o resultado.
    Se está processando, retorna status processing.
    Se não existe, retorna erro 404.
    
    Args:
        batch_id: ID do batch (ex: batch_20260330_153210_ab12cd)
        
    Returns:
        {
          "batch_id": "batch_...",
          "status": "completed",
          "summary": {...},
          "frames": [...]
        }
    """
    
    try:
        batch_dir = _get_batch_dir(batch_id)
        
        # Valida se o batch existe
        if not os.path.isdir(batch_dir):
            raise HTTPException(
                status_code=404,
                detail=f"Batch '{batch_id}' not found"
            )
        
        # Carrega status atual
        current_status = _load_batch_status(batch_id)
        
        # Se já está processando, avisa
        if current_status.get('status') == 'processing':
            raise HTTPException(
                status_code=409,  # Conflict
                detail="Diagnosis already in progress"
            )
        
        # Se já completou, retorna resultado
        if current_status.get('status') == 'completed':
            result_file = current_status.get('result_file')
            if result_file and os.path.exists(result_file):
                with open(result_file, 'r') as f:
                    result = json.load(f)
                return {
                    'batch_id': batch_id,
                    'status': 'completed',
                    **result
                }
        
        # ============================================================
        # INICIAR PROCESSAMENTO
        # ============================================================
        
        logger.info(f"Starting diagnosis for batch {batch_id}")
        
        # Marca como processando
        _save_batch_status(batch_id, 'processing')
        
        try:
            # Lista arquivos de imagem salvos (frame_*.jpg)
            frame_files = sorted([f for f in os.listdir(batch_dir) if f.startswith('frame_') and f.endswith('.jpg')])
            
            if not frame_files:
                raise Exception(f"No frames found in batch '{batch_id}'")
            
            logger.info(f"Processing {len(frame_files)} frames for batch {batch_id}")
            
            # Carrega as imagens do batch
            saved_images = []
            saved_filenames = []
            
            for frame_file in frame_files:
                try:
                    frame_path = os.path.join(batch_dir, frame_file)
                    img = Image.open(frame_path)
                    img.load()

                    try:
                        img = ImageOps.exif_transpose(img)
                    except Exception as exif_err:
                        logger.warning(f"EXIF transpose failed for saved image {frame_file}: {exif_err}")

                    if img.mode != "RGB":
                        img = img.convert("RGB")

                    saved_images.append(img.copy())
                    saved_filenames.append(frame_file)
                except Exception as e:
                    logger.error(f"Failed to load image {frame_file}: {e}")
            
            if not saved_images:
                raise Exception("No valid images could be loaded from batch")
            
            # Processa o diagnóstico
            diagnosis_result = _process_diagnose_batch_internal(saved_images, saved_filenames, batch_id)
            
            # Salva resultado e atualiza status para completed
            _save_batch_result(batch_id, diagnosis_result)
            
            logger.info(f"Diagnosis completed for batch {batch_id}")
            
            return {
                'batch_id': batch_id,
                'status': 'completed',
                **diagnosis_result
            }
            
        except Exception as e:
            logger.error(f"Error during diagnosis for batch {batch_id}: {e}")
            _save_batch_status(batch_id, 'failed', {'error': str(e)})
            raise HTTPException(status_code=500, detail=f"Diagnosis failed: {str(e)}")
        # Limpeza das imagens temporárias do batch
        finally:
            for f in os.listdir(batch_dir):
                if f.startswith('frame_') and f.endswith('.jpg'):
                    try:
                        os.remove(os.path.join(batch_dir, f))
                    except OSError as rm_err:
                        logger.warning(f"Could not delete {f}: {rm_err}")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in diagnose_batch_start: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/diagnose/batch/{batch_id}/status")
async def diagnose_batch_status(batch_id: str):
    """
    Consulta o status do diagnóstico de um batch.
    
    Returns:
        {
          "batch_id": "batch_...",
          "status": "uploaded|processing|completed|failed",
          "error": "..." (se failed)
        }
    """
    
    try:
        batch_dir = _get_batch_dir(batch_id)
        
        # Valida se o batch existe
        if not os.path.isdir(batch_dir):
            raise HTTPException(
                status_code=404,
                detail=f"Batch '{batch_id}' not found"
            )
        
        # Carrega status
        status_data = _load_batch_status(batch_id)
        
        return status_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error checking status for batch {batch_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/diagnose/batch/{batch_id}/result")
async def diagnose_batch_result(batch_id: str):
    """
    Busca o resultado do diagnóstico.
    
    Retorna o resultado completo se concluído.
    Retorna erro 202 se ainda não terminou.
    
    Returns:
        {
          "batch_id": "batch_...",
          "status": "completed",
          "summary": {...},
          "frames": [...]
        }
    """
    
    try:
        batch_dir = _get_batch_dir(batch_id)
        
        # Valida se o batch existe
        if not os.path.isdir(batch_dir):
            raise HTTPException(
                status_code=404,
                detail=f"Batch '{batch_id}' not found"
            )
        
        # Carrega status
        status_data = _load_batch_status(batch_id)
        
        if status_data.get('status') != 'completed':
            raise HTTPException(
                status_code=202,  # Accepted - still processing
                detail=f"Diagnosis not ready. Status: {status_data.get('status')}"
            )
        
        # Carrega resultado
        result_file = status_data.get('result_file')
        if not result_file or not os.path.exists(result_file):
            raise HTTPException(
                status_code=500,
                detail="Result file not found"
            )
        
        with open(result_file, 'r') as f:
            result = json.load(f)
        
        return {
            'batch_id': batch_id,
            'status': 'completed',
            **result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting result for batch {batch_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
# endpoint para upload e salvamento de múltiplas imagens em disco, com validação de formato e tamanho, e retorno de informações sobre os arquivos processados
@router.post("/upload/batch") 
async def upload_batch(files: List[UploadFile] = File(...)):
    """
    Upload and save multiple images to disk.
    
    Creates a batch_id and saves metadata/status for later processing.
    
    Args:
        files: List of image files (max 10)
        
    Returns:
        {
            "batch_id": "batch_20260330_153210_ab12cd",
            "status": "uploaded",
            "files_saved": 10
        }
    """

    try:
        max_batch_size: int = Config().get('api.max_batch_size', 10)
        if len(files) > max_batch_size:
            raise HTTPException(
                status_code=400,
                detail=f"Too many files. Max batch size: {max_batch_size}"
            )
        
        if len(files) == 0:
            raise HTTPException(status_code=400, detail="No files provided")
        
        # Gera batch_id único
        batch_id = _generate_batch_id()
        batch_dir = _get_batch_dir(batch_id)
        
        os.makedirs(batch_dir, exist_ok=True)
        
        # Lista para armazenar info dos arquivos salvos
        results = []
        successful_count = 0
        
        # Processa cada arquivo
        for i, file in enumerate(files):
            try:
                # Valida arquivo
                image = _validate_image_file(file)
                
                # Gera nome padronizado frame_00.jpg, frame_01.jpg, etc
                saved_filename = f"frame_{i:02d}.jpg"
                saved_path = os.path.join(batch_dir, saved_filename)
                
                # Salva imagem
                image.save(saved_path)
                
                results.append({
                    'filename': file.filename,
                    'saved_as': saved_filename,
                    'size_bytes': os.path.getsize(saved_path),
                    'image_size': f"{image.width}x{image.height}",
                    'status': 'success'
                })
                successful_count += 1
                
            except HTTPException as e:
                logger.error(f"Validation error for {file.filename}: {e.detail}")
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
        
        # Salva metadata e status iniciais
        _save_batch_metadata(batch_id, {
            'total_files': len(files),
            'files_saved': successful_count,
            'results': results
        })
        
        _save_batch_status(batch_id, 'uploaded', {
            'created_at': datetime.now().isoformat()
        })
        
        logger.info(f"Batch {batch_id} created with {successful_count}/{len(files)} files")
        
        return {
            'batch_id': batch_id,
            'status': 'uploaded',
            'files_saved': successful_count,
            'message': f'Saved {successful_count}/{len(files)} files'
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading batch: {e}")
        raise HTTPException(status_code=500, detail=f"Error uploading batch: {str(e)}")

