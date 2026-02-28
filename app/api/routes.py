"""
API Routes for AR Diagnostic MVP
Illumination-only endpoints
"""

import logging
import os
from typing import List, Optional
from datetime import datetime
from pathlib import Path
from fastapi import APIRouter, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
from PIL import Image
import io

from app.pipeline.illumination_pipeline import IlluminationPipeline
from app.config.config import Config

logger = logging.getLogger(__name__)

router = APIRouter()

# Global pipeline instance (injected by main.py)
_pipeline: Optional[IlluminationPipeline] = None


def set_pipeline(pipeline: IlluminationPipeline):
    """Set global pipeline instance"""
    global _pipeline
    _pipeline = pipeline


def get_pipeline() -> IlluminationPipeline:
    """Get global pipeline instance"""
    if _pipeline is None:
        raise HTTPException(status_code=503, detail="Pipeline not initialized")
    return _pipeline


def _validate_image_file(file: UploadFile) -> Image.Image:
    """
    Validate and load image from upload
    
    Args:
        file: Uploaded file
        
    Returns:
        PIL Image
        
    Raises:
        HTTPException: If file is invalid
    """
    # Check file extension
    allowed_formats = ['jpg', 'jpeg', 'png', 'bmp']
    file_ext = file.filename.split('.')[-1].lower()
    
    if file_ext not in allowed_formats:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file format. Allowed: {', '.join(allowed_formats)}"
        )
    
    # Read and validate image
    try:
        contents = file.file.read()
        image = Image.open(io.BytesIO(contents))
        
        # Validate image size
        max_size = 10 * 1024 * 1024  # 10MB
        if len(contents) > max_size:
            raise HTTPException(
                status_code=400,
                detail=f"File too large. Max size: {max_size / 1024 / 1024}MB"
            )
        
        return image
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid image file: {str(e)}")
    finally:
        file.file.seek(0)


@router.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "AR Diagnostic MVP - Illumination Analysis",
        "version": "0.1.0",
        "endpoints": {
            "health": "GET - Check API health",
            "diagnose": "POST - Diagnose single image (with LLM)",
            "batch": "POST - Diagnose multiple images (with LLM)",
            "metrics": "POST - Extract metrics only (no LLM)",
            "upload": "POST - Upload and save single image",
            "upload_batch": "POST - Upload and save multiple images",
            "docs": "GET - Interactive API documentation (Swagger)"
        }
    }


@router.get("/health")
async def health():
    """Health check endpoint"""
    try:
        pipeline = get_pipeline()
        return {
            "status": "healthy",
            "model": pipeline.model_type,
            "device": pipeline.device,
            "quantization": "4-bit" if pipeline.use_4bit else "fp16/fp32"
        }
    except Exception as e:
        return JSONResponse(
            status_code=503,
            content={"status": "unhealthy", "error": str(e)}
        )


@router.post("/diagnose")
async def diagnose_image(file: UploadFile = File(...)):
    """
    Diagnose single image for illumination quality
    
    Args:
        file: Image file (jpg, png, bmp)
        
    Returns:
        Diagnostic result with status, metrics, and explanation
    """
    try:
        # Validate and load image
        image = _validate_image_file(file)
        
        # Get pipeline
        pipeline = get_pipeline()
        
        # Diagnose
        result = pipeline.diagnose(image)
        
        # Add metadata
        result['filename'] = file.filename
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing image: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing image: {str(e)}")


@router.post("/diagnose/batch")
async def diagnose_batch(files: List[UploadFile] = File(...)):
    """
    Diagnose multiple images in batch
    
    Args:
        files: List of image files (max 10)
        
    Returns:
        List of diagnostic results
    """
    try:
        # Validate batch size
        max_batch_size = 10
        if len(files) > max_batch_size:
            raise HTTPException(
                status_code=400,
                detail=f"Too many files. Max batch size: {max_batch_size}"
            )
        
        if len(files) == 0:
            raise HTTPException(status_code=400, detail="No files provided")
        
        # Get pipeline
        pipeline = get_pipeline()
        
        # Process each image
        results = []
        for file in files:
            try:
                # Validate and load image
                image = _validate_image_file(file)
                
                # Diagnose
                result = pipeline.diagnose(image)
                result['filename'] = file.filename
                result['status_code'] = 200
                
                results.append(result)
                
            except HTTPException as e:
                # Add error result for this file
                results.append({
                    'filename': file.filename,
                    'status_code': e.status_code,
                    'error': e.detail
                })
            except Exception as e:
                logger.error(f"Error processing {file.filename}: {e}")
                results.append({
                    'filename': file.filename,
                    'status_code': 500,
                    'error': str(e)
                })
        
        return {
            'total': len(files),
            'successful': sum(1 for r in results if r.get('status_code', 200) == 200),
            'failed': sum(1 for r in results if r.get('status_code', 200) != 200),
            'results': results
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing batch: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing batch: {str(e)}")


@router.post("/metrics")
async def extract_metrics(file: UploadFile = File(...)):
    """
    Extract illumination metrics only (no LLM diagnosis)
    
    Args:
        file: Image file (jpg, png, bmp)
        
    Returns:
        Metrics without LLM explanation (faster)
    """
    try:
        # Validate and load image
        image = _validate_image_file(file)
        
        # Get pipeline
        pipeline = get_pipeline()
        
        # Extract metrics only (no LLM)
        metrics = pipeline.extract_metrics(image)
        
        # Add metadata
        result = {
            'filename': file.filename,
            'metrics': metrics
        }
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error extracting metrics: {e}")
        raise HTTPException(status_code=500, detail=f"Error extracting metrics: {str(e)}")


@router.post("/upload")
async def upload_image(file: UploadFile = File(...)):
    """
    Upload and save single image to disk
    
    Args:
        file: Image file (jpg, png, bmp)
        
    Returns:
        Saved file info
    """
    try:
        # Validate file
        image = _validate_image_file(file)
        
        # Get upload directory from config
        config = Config()
        upload_dir = config.get('api.upload_dir', 'data/uploads')
        
        # Create upload directory
        os.makedirs(upload_dir, exist_ok=True)
        
        # Generate unique filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_ext = Path(file.filename).suffix
        saved_filename = f"{timestamp}_{file.filename}"
        saved_path = os.path.join(upload_dir, saved_filename)
        
        # Save image
        image.save(saved_path)
        
        return {
            'filename': file.filename,
            'saved_as': saved_filename,
            'path': saved_path,
            'size_bytes': os.path.getsize(saved_path),
            'image_size': f"{image.width}x{image.height}"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading image: {e}")
        raise HTTPException(status_code=500, detail=f"Error uploading image: {str(e)}")


@router.post("/upload/batch")
async def upload_batch(files: List[UploadFile] = File(...)):
    """
    Upload and save multiple images to disk
    
    Args:
        files: List of image files (max 10)
        
    Returns:
        List of saved file info
    """
    try:
        # Validate batch size
        max_batch_size = 10
        if len(files) > max_batch_size:
            raise HTTPException(
                status_code=400,
                detail=f"Too many files. Max batch size: {max_batch_size}"
            )
        
        if len(files) == 0:
            raise HTTPException(status_code=400, detail="No files provided")
        
        # Get upload directory from config
        config = Config()
        upload_dir = config.get('api.upload_dir', 'data/uploads')
        
        # Create upload directory
        os.makedirs(upload_dir, exist_ok=True)
        
        # Process each file
        results = []
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        for i, file in enumerate(files):
            try:
                # Validate file
                image = _validate_image_file(file)
                
                # Generate unique filename
                file_ext = Path(file.filename).suffix
                saved_filename = f"{timestamp}_{i:02d}_{file.filename}"
                saved_path = os.path.join(upload_dir, saved_filename)
                
                # Save image
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
