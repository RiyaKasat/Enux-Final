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
        # Update status not needed for playbook_files
        # supabase_service.update_upload_status(upload_id, "processing")
        
        # Extract content
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        extracted_data = loop.run_until_complete(extract_content_from_file(file_path, mime_type))
        
        # Step 2: Classify blocks into playbook assets using AI
        from services.ai_processor import classify_content_blocks, generate_embeddings, generate_playbook_suggestions
        
        print(f"📝 Extracted {len(extracted_data['blocks'])} content blocks")
        
        # Classify blocks into playbook asset types
        classified_blocks = classify_content_blocks(extracted_data["blocks"])
        print(f"🏷️ Classified blocks into playbook assets")
        
        # Step 3: Generate embeddings for each block
        blocks_with_embeddings = generate_embeddings(classified_blocks)
        print(f"🧠 Generated embeddings for {len(blocks_with_embeddings)} blocks")
        
        # Step 4: Generate playbook structure suggestions
        playbook_suggestions = generate_playbook_suggestions(blocks_with_embeddings)
        print(f"📋 Generated playbook structure with {len(playbook_suggestions['sections'])} sections")
        
        # Step 5: Store embeddings and update playbook with tags
        all_tags = set()
        for block in blocks_with_embeddings:
            all_tags.update(block.get("tags", []))
        
        # Store embeddings in database
        supabase_service.store_embeddings(upload_id, blocks_with_embeddings)
        
        # Update playbook with extracted tags
        # First get the playbook ID associated with this file
        file_data = supabase_service.get_playbook_file_by_id(upload_id)
        if file_data.get("success") and file_data.get("data"):
            playbook_id = file_data["data"].get("playbook_id")
            if playbook_id:
                supabase_service.update_playbook_tags(playbook_id, list(all_tags))
        
        print(f"💾 Stored {len(blocks_with_embeddings)} embeddings and {len(all_tags)} tags")
        
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
        # Update status not needed for playbook_files
        # supabase_service.update_upload_status(upload_id, "processing")
        
        # Extract content from URL
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        extracted_data = loop.run_until_complete(extract_content_from_url(url))
        
        # For demo, we'll just store the blocks as-is (without AI processing)
        processed_blocks = extracted_data["blocks"]
        
        # Store content blocks
        # Content blocks are not in schema - skipping for now
        # supabase_service.create_content_blocks(upload_id, processed_blocks)
        
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
        
        # Create playbook file record in Supabase database
        # First, create a default playbook if none exists
        playbook_result = supabase_service.get_all_playbooks(limit=1)
        if playbook_result["success"] and playbook_result["data"]:
            playbook_id = playbook_result["data"][0]["id"]
        else:
            # Create a default playbook for uploaded files
            default_playbook = {
                "title": "Uploaded Files Playbook",
                "description": "Default playbook for uploaded files",
                "tags": ["uploads"],
                "stage": "draft"
            }
            playbook_create_result = supabase_service.create_playbook(default_playbook)
            if playbook_create_result["success"]:
                playbook_id = playbook_create_result["data"]["id"]
            else:
                return jsonify({"error": "Failed to create playbook for file"}), 500

        file_data = {
            "id": upload_id,
            "file_name": filename,
            "file_type": os.path.splitext(filename)[1].lower().replace('.', '') or 'txt',
            "storage_path": upload_result["path"],
            "playbook_id": playbook_id
        }
        
        db_result = supabase_service.create_playbook_file(file_data)
        
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
            "redirect_url": f"/playbook/{upload_id}",
            "file_data": db_result.get("data", {})
        })
    
    except Exception as e:
        if 'file_path' in locals() and os.path.exists(file_path):
            os.remove(file_path)
        import traceback
        print(f"❌ Upload error: {str(e)}")
        print(f"❌ Full traceback: {traceback.format_exc()}")
        return jsonify({"error": f"Upload failed: {str(e)}", "details": traceback.format_exc()}), 500

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
        
        # Create a default playbook for URL content
        playbook_result = supabase_service.get_all_playbooks(limit=1)
        if playbook_result["success"] and playbook_result["data"]:
            playbook_id = playbook_result["data"][0]["id"]
        else:
            default_playbook = {
                "title": "URL Content Playbook",
                "description": "Default playbook for URL content",
                "tags": ["url", "web"],
                "stage": "draft"
            }
            playbook_create_result = supabase_service.create_playbook(default_playbook)
            if playbook_create_result["success"]:
                playbook_id = playbook_create_result["data"]["id"]
            else:
                return jsonify({"error": "Failed to create playbook for URL"}), 500

        file_data = {
            "id": upload_id,
            "file_name": url.split("/")[-1] or "webpage",
            "file_type": "txt",
            "storage_path": url,
            "playbook_id": playbook_id
        }
        
        db_result = supabase_service.create_playbook_file(file_data)
        
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
        result = supabase_service.get_playbook_file_by_id(upload_id)
        
        if not result["success"]:
            return jsonify({"error": result["error"]}), 404
        
        upload = result["data"]
        if not upload:
            return jsonify({"error": "Upload not found"}), 404
        
        # Get blocks count if completed
        blocks_count = 0
        # playbook_files don't have status, so always show blocks count as 0
        # Content blocks not in schema - return empty for now
        blocks_result = {"success": True, "data": []}
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
        # Content blocks not in schema - return empty for now
        result = {"success": True, "data": []}
        
        if not result["success"]:
            return jsonify({"error": result["error"]}), 500
        
        return jsonify({"blocks": result["data"]})
    
    except Exception as e:
        return jsonify({"error": f"Failed to get blocks: {str(e)}"}), 500

@app.route('/api/dashboard/stats')
def get_dashboard_stats():
    """Get dashboard statistics"""
    
    try:
        uploads_result = supabase_service.get_all_playbook_files(limit=100)
        
        if not uploads_result["success"]:
            return jsonify({"error": uploads_result["error"]}), 500
        
        files = uploads_result["data"]
        
        total_playbooks = len(files)
        active_projects = len(files)  # All files are considered active since no status field
        total_size = 0  # file_size not in playbook_files schema
        
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
        result = supabase_service.get_all_playbook_files(limit=5)
        
        if not result["success"]:
            return jsonify({"error": result["error"]}), 500
        
        return jsonify({"playbooks": result["data"]})
    
    except Exception as e:
        return jsonify({"error": f"Failed to get recent playbooks: {str(e)}"}), 500

if __name__ == "__main__":
    print("✅ Starting PlaybookOS Flask server...")
    port = int(os.getenv("FLASK_PORT", 8001))
    host = os.getenv("FLASK_HOST", "0.0.0.0")
    debug = os.getenv("FLASK_DEBUG", "true").lower() == "true"
    app.run(host=host, port=port, debug=debug)
