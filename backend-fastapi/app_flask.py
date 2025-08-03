from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
import uuid
import json
from datetime import datetime
from threading import Thread
import time
from werkzeug.utils import secure_filename
from services.supabase_service import supabase_service
from services.content_extractor import extract_content_from_file, extract_content_from_url

app = Flask(__name__)
CORS(app)

# Configuration
UPLOAD_DIR = os.getenv("UPLOAD_DIR", "./uploads")
MAX_FILE_SIZE = int(os.getenv("MAX_FILE_SIZE", "10485760"))  # 10MB
ALLOWED_EXTENSIONS = {".pdf", ".txt", ".md", ".docx"}

# Ensure upload directory exists
os.makedirs(UPLOAD_DIR, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and \
           os.path.splitext(filename)[1].lower() in ALLOWED_EXTENSIONS

def process_upload_background(upload_id, file_path, mime_type):
    """Background task to process uploaded file"""
    try:
        # Update status to processing
        supabase_service.update_upload_status(upload_id, "processing")
        
        # Extract content
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        extracted_data = loop.run_until_complete(extract_content_from_file(file_path, mime_type))
        
        # For demo, we'll just store the blocks as-is (without AI processing)
        processed_blocks = extracted_data["blocks"]
        
        # Store content blocks
        supabase_service.create_content_blocks(upload_id, processed_blocks)
        
        # Update upload status
        supabase_service.update_upload_status(upload_id, "completed")
        
        loop.close()
        
    except Exception as e:
        # Update status to failed
        supabase_service.update_upload_status(upload_id, "failed", str(e))

def process_url_background(upload_id, url):
    """Background task to process URL import"""
    try:
        # Update status to processing
        supabase_service.update_upload_status(upload_id, "processing")
        
        # Extract content from URL
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        extracted_data = loop.run_until_complete(extract_content_from_url(url))
        
        # For demo, we'll just store the blocks as-is (without AI processing)
        processed_blocks = extracted_data["blocks"]
        
        # Store content blocks
        supabase_service.create_content_blocks(upload_id, processed_blocks)
        
        # Update upload status
        supabase_service.update_upload_status(upload_id, "completed")
        
        loop.close()
        
    except Exception as e:
        # Update status to failed
        supabase_service.update_upload_status(upload_id, "failed", str(e))

@app.route('/')
def root():
    return {"message": "PlaybookOS API is running"}

@app.route('/health')
def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}

@app.route('/api/upload/file', methods=['POST'])
def upload_file():
    """Upload and process a file"""
    
    # Check if file is in request
    if 'file' not in request.files:
        return jsonify({"error": "No file provided"}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No file selected"}), 400
    
    if not allowed_file(file.filename):
        return jsonify({
            "error": f"File type not allowed. Supported: {', '.join(ALLOWED_EXTENSIONS)}"
        }), 400
    
    try:
        # Generate unique filename and save file locally first
        upload_id = str(uuid.uuid4())
        filename = secure_filename(file.filename)
        unique_filename = f"{upload_id}_{filename}"
        file_path = os.path.join(UPLOAD_DIR, unique_filename)
        
        file.save(file_path)
        file_size = os.path.getsize(file_path)
        
        if file_size > MAX_FILE_SIZE:
            os.remove(file_path)
            return jsonify({"error": "File size exceeds 10MB limit"}), 400
        
        # Upload to Supabase Storage
        upload_result = supabase_service.upload_file(file_path, filename)
        
        if not upload_result["success"]:
            os.remove(file_path)
            return jsonify({"error": f"File upload failed: {upload_result['error']}"}), 500
        
        # Create upload record in Supabase database
        upload_data = {
            "id": upload_id,
            "filename": unique_filename,
            "original_name": filename,
            "file_path": upload_result["path"],
            "file_size": file_size,
            "mime_type": file.content_type,
            "storage_url": upload_result["public_url"],
            "status": "uploaded",
            "created_at": datetime.utcnow().isoformat()
        }
        
        db_result = supabase_service.create_upload_record(upload_data)
        
        if not db_result["success"]:
            os.remove(file_path)
            return jsonify({"error": f"Database record creation failed: {db_result['error']}"}), 500
        
        # Start background processing
        thread = Thread(target=process_upload_background, args=(upload_id, file_path, file.content_type))
        thread.daemon = True
        thread.start()
        
        return jsonify({
            "success": True,
            "upload_id": upload_id,
            "message": "File uploaded successfully, processing started",
            "redirect_url": f"/playbook/{upload_id}"
        })
    
    except Exception as e:
        if 'file_path' in locals() and os.path.exists(file_path):
            os.remove(file_path)
        return jsonify({"error": f"Upload failed: {str(e)}"}), 500

@app.route('/api/upload/url', methods=['POST'])
def import_url():
    """Import content from a URL"""
    
    data = request.get_json()
    if not data or 'url' not in data:
        return jsonify({"error": "URL is required"}), 400
    
    url = data['url']
    title = data.get('title', 'URL Import')
    
    try:
        upload_id = str(uuid.uuid4())
        
        # Store URL upload record
        upload_data = {
            "id": upload_id,
            "source_url": url,
            "original_name": title,
            "status": "uploaded",
            "created_at": datetime.utcnow().isoformat()
        }
        
        db_result = supabase_service.create_upload_record(upload_data)
        
        if not db_result["success"]:
            return jsonify({"error": f"Database record creation failed: {db_result['error']}"}), 500
        
        # Start background processing
        thread = Thread(target=process_url_background, args=(upload_id, url))
        thread.daemon = True
        thread.start()
        
        return jsonify({
            "success": True,
            "upload_id": upload_id,
            "message": "URL import started, processing in background",
            "redirect_url": f"/playbook/{upload_id}"
        })
    
    except Exception as e:
        return jsonify({"error": f"URL import failed: {str(e)}"}), 500

@app.route('/api/upload/<upload_id>/status')
def get_upload_status(upload_id):
    """Get upload status and details"""
    
    try:
        result = supabase_service.get_upload_by_id(upload_id)
        
        if not result["success"]:
            return jsonify({"error": result["error"]}), 404
        
        upload = result["data"]
        if not upload:
            return jsonify({"error": "Upload not found"}), 404
        
        # Get blocks count if completed
        blocks_count = 0
        if upload["status"] == "completed":
            blocks_result = supabase_service.get_content_blocks(upload_id)
            if blocks_result["success"]:
                blocks_count = len(blocks_result["data"])
        
        upload["blocks_extracted"] = blocks_count
        
        return jsonify(upload)
    
    except Exception as e:
        return jsonify({"error": f"Failed to get status: {str(e)}"}), 500

@app.route('/api/playbook/<upload_id>/blocks')
def get_playbook_blocks(upload_id):
    """Get extracted content blocks for a playbook"""
    
    try:
        result = supabase_service.get_content_blocks(upload_id)
        
        if not result["success"]:
            return jsonify({"error": result["error"]}), 500
        
        return jsonify({"blocks": result["data"]})
    
    except Exception as e:
        return jsonify({"error": f"Failed to get blocks: {str(e)}"}), 500

@app.route('/api/dashboard/stats')
def get_dashboard_stats():
    """Get dashboard statistics"""
    
    try:
        uploads_result = supabase_service.get_all_uploads(limit=100)
        
        if not uploads_result["success"]:
            return jsonify({"error": uploads_result["error"]}), 500
        
        uploads = uploads_result["data"]
        
        total_playbooks = len(uploads)
        active_projects = len([u for u in uploads if u["status"] == "completed"])
        total_size = sum(u.get("file_size", 0) for u in uploads)
        
        return jsonify({
            "total_playbooks": total_playbooks,
            "active_projects": active_projects,
            "total_collaborators": 1,  # Mock for now
            "storage_used": f"{total_size / (1024*1024):.1f} MB"
        })
    
    except Exception as e:
        return jsonify({"error": f"Failed to get stats: {str(e)}"}), 500

@app.route('/api/dashboard/recent')
def get_recent_playbooks():
    """Get recent playbooks"""
    
    try:
        result = supabase_service.get_all_uploads(limit=5)
        
        if not result["success"]:
            return jsonify({"error": result["error"]}), 500
        
        return jsonify({"playbooks": result["data"]})
    
    except Exception as e:
        return jsonify({"error": f"Failed to get recent playbooks: {str(e)}"}), 500

if __name__ == "__main__":
    print("✅ Starting PlaybookOS Flask server...")
    app.run(host='0.0.0.0', port=8001, debug=True)
