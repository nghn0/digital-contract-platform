# app/api/routes.py
"""
API routes for LegalT contract analysis.

⚠️  SECURITY:
    - Never commit .env file containing API keys. Use environment variables only.
    - File uploads are validated for size (50MB max) and type (PDF, DOCX, TXT only).
    - All uploaded files are processed in secure temporary directories and auto-deleted.
    - Requests timeout after 5 minutes to prevent resource exhaustion.
"""
from fastapi import APIRouter, UploadFile, File, HTTPException
import asyncio
import os
from pathlib import Path
from tempfile import TemporaryDirectory
from services.pipeline import run_pipeline
from models.schema import LegalDocumentAnalysis

# ─── Security Constants ──────────────────────────────────────────────────────
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB
MAX_FILENAME_LENGTH = 255
ALLOWED_EXTENSIONS = {".pdf", ".docx", ".doc", ".txt"}
REQUEST_TIMEOUT_SECONDS = 300  # 5 minutes

router = APIRouter()


@router.post("/analyze", response_model=LegalDocumentAnalysis)
async def analyze_contract(file: UploadFile = File(...)):
    """
    Main analysis endpoint.
    Accepts PDF/DOCX/TXT and runs the centralized LegalT pipeline.
    
    Args:
        file: Contract file to analyze (PDF, DOCX, DOC, or TXT)
        
    Returns:
        LegalDocumentAnalysis: Complete analysis output
        
    Raises:
        HTTPException 400: Invalid file type, name, or extension
        HTTPException 413: File exceeds size limit
        HTTPException 504: Request timeout (document too large or LLM unresponsive)
    """
    allowed_types = [
        "application/pdf",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "text/plain"
    ]
    
    # 2A: Validate content type (existing check — preserve it)
    if file.content_type not in allowed_types:
        raise HTTPException(400, f"Unsupported file type: {file.content_type}")
    
    # 2C: Validate filename
    if not file.filename or len(file.filename) > MAX_FILENAME_LENGTH:
        raise HTTPException(400, "Invalid filename")
    
    suffix = Path(file.filename).suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file extension '{suffix}'. Allowed: {ALLOWED_EXTENSIONS}"
        )
    
    # 2B: Read with size limit
    try:
        content = await asyncio.wait_for(
            file.read(MAX_FILE_SIZE + 1),
            timeout=30.0
        )
    except asyncio.TimeoutError:
        raise HTTPException(504, "File read timeout — file too large")
    
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail=f"File size exceeds maximum allowed {MAX_FILE_SIZE} bytes"
        )
    
    # 2D: Use TemporaryDirectory for secure temp file handling
    try:
        with TemporaryDirectory() as tmpdir:
            tmp_path = os.path.join(tmpdir, f"upload{suffix}")
            with open(tmp_path, 'wb') as f:
                f.write(content)
            
            try:
                # Run the same orchestrated pipeline used by the CLI.
                # This keeps LLM provider/model selection and validation centralized.
                return await asyncio.wait_for(
                    asyncio.to_thread(run_pipeline, tmp_path, False),
                    timeout=REQUEST_TIMEOUT_SECONDS
                )
            except asyncio.TimeoutError:
                raise HTTPException(
                    status_code=504,
                    detail="Request timeout — document too large or LLM unresponsive"
                )
            # Auto-cleanup when TemporaryDirectory context exits
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Pipeline error: {str(e)}"
        )


@router.get("/report/{document_id}")
async def get_report(document_id: str):
    """Fetch a previously analyzed report from Supabase."""
    # TODO: query Supabase by document_id
    pass