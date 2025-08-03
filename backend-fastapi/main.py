from fastapi import FastAPI, File, UploadFile, HTTPException, Form, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import os
import uuid
import aiofiles
from typing import Optional
import asyncio
from datetime import datetime
import json

from services.database import get_db_connection, init_database
from services.content_extractor import extract_content_from_file, extract_content_from_url
from services.ai_processor import process_content_blocks
from models.schemas import UploadStatus, UploadResponse

app = FastAPI(
    title="PlaybookOS API",
    description="API for GitHub-style collaboration on business playbooks",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration
UPLOAD_DIR = os.getenv("UPLOAD_DIR", "./uploads")
MAX_FILE_SIZE = int(os.getenv("MAX_FILE_SIZE", "10485760"))  # 10MB
ALLOWED_EXTENSIONS = {".pdf", ".txt", ".md", ".docx"}

# Ensure upload directory exists
os.makedirs(UPLOAD_DIR, exist_ok=True)

@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    await init_database()

class URLImportRequest(BaseModel):
    url: str
    title: Optional[str] = None
    description: Optional[str] = None

@app.get("/")
async def root():
    return {"message": "PlaybookOS API is running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}

async def process_upload_background(upload_id: str, file_path: str, mime_type: str):
    """Background task to process uploaded file"""
    try:
        # Update status to processing
        async with get_db_connection() as conn:
            await conn.execute(
                "UPDATE uploads SET status = $1, updated_at = NOW() WHERE id = $2",
                "processing", upload_id
            )
        
        # Extract content
        extracted_data = await extract_content_from_file(file_path, mime_type)
        
        # Process with AI
        processed_blocks = await process_content_blocks(extracted_data["blocks"])
        
        # Store content blocks
        async with get_db_connection() as conn:
            for block in processed_blocks:
                await conn.execute("""
                    INSERT INTO content_blocks 
                    (id, upload_id, type, content, confidence_score, suggested_asset_type, created_at)
                    VALUES ($1, $2, $3, $4, $5, $6, NOW())
                """, 
                    str(uuid.uuid4()), upload_id, block["type"], block["content"],
                    block.get("confidence_score", 0.8), block.get("suggested_asset_type")
                )
            
            # Update upload status
            await conn.execute(
                "UPDATE uploads SET status = $1, processed_at = NOW() WHERE id = $2",
                "completed", upload_id
            )
    
    except Exception as e:
        # Update status to failed
        async with get_db_connection() as conn:
            await conn.execute(
                "UPDATE uploads SET status = $1, error_message = $2 WHERE id = $3",
                "failed", str(e), upload_id
            )

@app.post("/api/upload/file", response_model=UploadResponse)
async def upload_file(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    title: Optional[str] = Form(None),
    description: Optional[str] = Form(None)
):
    """Upload and process a file"""
    
    # Validate file
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")
    
    file_ext = os.path.splitext(file.filename)[1].lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400, 
            detail=f"File type {file_ext} not allowed. Supported: {', '.join(ALLOWED_EXTENSIONS)}"
        )
    
    # Check file size
    file_size = 0
    content = await file.read()
    file_size = len(content)
    
    if file_size > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File size exceeds 10MB limit")
    
    # Generate unique filename and save file
    upload_id = str(uuid.uuid4())
    unique_filename = f"{upload_id}_{file.filename}"
    file_path = os.path.join(UPLOAD_DIR, unique_filename)
    
    async with aiofiles.open(file_path, 'wb') as f:
        await f.write(content)
    
    try:
        # Store upload record
        async with get_db_connection() as conn:
            await conn.execute("""
                INSERT INTO uploads 
                (id, filename, original_name, file_path, file_size, mime_type, status, created_at)
                VALUES ($1, $2, $3, $4, $5, $6, $7, NOW())
            """, 
                upload_id, unique_filename, file.filename, file_path,
                file_size, file.content_type, "uploaded"
            )
        
        # Start background processing
        background_tasks.add_task(
            process_upload_background, upload_id, file_path, file.content_type
        )
        
        return UploadResponse(
            success=True,
            upload_id=upload_id,
            message="File uploaded successfully, processing started",
            redirect_url=f"/playbook/{upload_id}"
        )
    
    except Exception as e:
        # Clean up file if database insert fails
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

async def process_url_background(upload_id: str, url: str):
    """Background task to process URL import"""
    try:
        # Update status to processing
        async with get_db_connection() as conn:
            await conn.execute(
                "UPDATE uploads SET status = $1, updated_at = NOW() WHERE id = $2",
                "processing", upload_id
            )
        
        # Extract content from URL
        extracted_data = await extract_content_from_url(url)
        
        # Process with AI
        processed_blocks = await process_content_blocks(extracted_data["blocks"])
        
        # Store content blocks
        async with get_db_connection() as conn:
            for block in processed_blocks:
                await conn.execute("""
                    INSERT INTO content_blocks 
                    (id, upload_id, type, content, confidence_score, suggested_asset_type, created_at)
                    VALUES ($1, $2, $3, $4, $5, $6, NOW())
                """, 
                    str(uuid.uuid4()), upload_id, block["type"], block["content"],
                    block.get("confidence_score", 0.8), block.get("suggested_asset_type")
                )
            
            # Update upload status
            await conn.execute(
                "UPDATE uploads SET status = $1, processed_at = NOW() WHERE id = $2",
                "completed", upload_id
            )
    
    except Exception as e:
        # Update status to failed
        async with get_db_connection() as conn:
            await conn.execute(
                "UPDATE uploads SET status = $1, error_message = $2 WHERE id = $3",
                "failed", str(e), upload_id
            )

@app.post("/api/upload/url", response_model=UploadResponse)
async def import_url(request: URLImportRequest, background_tasks: BackgroundTasks):
    """Import content from a URL"""
    
    upload_id = str(uuid.uuid4())
    
    try:
        # Store URL upload record
        async with get_db_connection() as conn:
            await conn.execute("""
                INSERT INTO uploads 
                (id, source_url, original_name, status, created_at)
                VALUES ($1, $2, $3, $4, NOW())
            """, 
                upload_id, request.url, request.title or "URL Import", "uploaded"
            )
        
        # Start background processing
        background_tasks.add_task(process_url_background, upload_id, request.url)
        
        return UploadResponse(
            success=True,
            upload_id=upload_id,
            message="URL import started, processing in background",
            redirect_url=f"/playbook/{upload_id}"
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"URL import failed: {str(e)}")

@app.get("/api/upload/{upload_id}/status")
async def get_upload_status(upload_id: str):
    """Get upload status and details"""
    
    try:
        async with get_db_connection() as conn:
            # Get upload details
            upload = await conn.fetchrow(
                "SELECT * FROM uploads WHERE id = $1", upload_id
            )
            
            if not upload:
                raise HTTPException(status_code=404, detail="Upload not found")
            
            # Get blocks count if completed
            blocks_count = 0
            if upload["status"] == "completed":
                result = await conn.fetchrow(
                    "SELECT COUNT(*) as count FROM content_blocks WHERE upload_id = $1",
                    upload_id
                )
                blocks_count = result["count"] if result else 0
            
            return {
                **dict(upload),
                "blocks_extracted": blocks_count
            }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get status: {str(e)}")

@app.get("/api/playbook/{upload_id}/blocks")
async def get_playbook_blocks(upload_id: str):
    """Get extracted content blocks for a playbook"""
    
    try:
        async with get_db_connection() as conn:
            blocks = await conn.fetch(
                "SELECT * FROM content_blocks WHERE upload_id = $1 ORDER BY created_at",
                upload_id
            )
            
            return {"blocks": [dict(block) for block in blocks]}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get blocks: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
