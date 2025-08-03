import os
from typing import Dict, List, Any, Optional
import uuid
from datetime import datetime
import mimetypes
import requests
import json
from dotenv import load_dotenv
import urllib3

# Suppress SSL warnings for corporate networks
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

load_dotenv()

class SupabaseService:
    """Supabase service for file storage and database operations (HTTP-only)"""
    
    def __init__(self):
        self.url = os.getenv('SUPABASE_URL')
        self.key = os.getenv('SUPABASE_KEY')
        self.service_key = os.getenv('SUPABASE_SERVICE_KEY')
        
        # Check if credentials are provided and valid
        if (not self.url or not self.key or 
            self.url == 'your_supabase_project_url_here' or 
            self.key == 'your_supabase_anon_key_here'):
            print("⚠️ Supabase credentials not configured, using mock storage")
            self.client = None
        else:
            try:
                # Use direct HTTP requests instead of supabase-py to avoid WebSocket issues
                self.headers = {
                    'apikey': self.key,
                    'Authorization': f'Bearer {self.key}',
                    'Content-Type': 'application/json',
                    'Accept': 'application/json',
                    'User-Agent': 'playbook-platform/1.0'
                }
                
                # Test connection with a simple request (disable SSL verification for corporate networks)
                test_response = requests.get(
                    f"{self.url}/rest/v1/",
                    headers=self.headers,
                    timeout=10,
                    verify=False  # Disable SSL verification for corporate networks
                )
                
                if test_response.status_code < 400:
                    self.client = "http_client"  # Mark as using HTTP client
                    print("✅ Supabase HTTP client initialized (no WebSocket/realtime)")
                else:
                    print(f"⚠️ Supabase connection failed: {test_response.status_code}")
                    self.client = None
                    
            except Exception as e:
                print(f"⚠️ Failed to initialize Supabase HTTP client: {e}")
                print("Using mock storage instead")
                self.client = None
    
    def upload_file(self, file_path: str, file_name: str, bucket_name: str = "playbooks") -> Dict[str, Any]:
        """Upload file to Supabase Storage using HTTP API"""
        if not self.client:
            # Mock response for development
            return {
                "success": True,
                "public_url": f"mock://storage/{bucket_name}/{file_name}",
                "path": f"{bucket_name}/{file_name}"
            }
        
        try:
            # Read file content
            with open(file_path, 'rb') as f:
                file_content = f.read()
            
            # Generate unique file path
            file_extension = os.path.splitext(file_name)[1]
            unique_name = f"{uuid.uuid4()}{file_extension}"
            storage_path = f"uploads/{unique_name}"
            
            # Upload to Supabase Storage using REST API
            upload_url = f"{self.url}/storage/v1/object/{bucket_name}/{storage_path}"
            
            upload_headers = {
                'apikey': self.key,
                'Authorization': f'Bearer {self.key}',
                'Content-Type': mimetypes.guess_type(file_name)[0] or "application/octet-stream",
                'User-Agent': 'playbook-platform/1.0'
            }
            
            response = requests.post(
                upload_url,
                data=file_content,
                headers=upload_headers,
                timeout=30,
                verify=False  # Disable SSL verification
            )
            
            if response.status_code in [200, 201]:
                # Get public URL for the uploaded file
                public_url = f"{self.url}/storage/v1/object/public/{bucket_name}/{storage_path}"
                
                return {
                    "success": True,
                    "public_url": public_url,
                    "path": storage_path,
                    "storage_response": response.json() if response.content else {}
                }
            else:
                error_msg = "Upload failed"
                try:
                    error_data = response.json()
                    error_msg = error_data.get('message', error_msg)
                except:
                    error_msg = f"HTTP {response.status_code}: {response.text}"
                
                return {
                    "success": False,
                    "error": error_msg
                }
        
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def create_upload_record(self, upload_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create upload record in Supabase database"""
        if not self.client:
            # Mock response for development
            upload_id = str(uuid.uuid4())
            return {
                "success": True,
                "data": {"id": upload_id, **upload_data},
                "upload_id": upload_id
            }
        
        try:
            # Insert record using REST API
            insert_url = f"{self.url}/rest/v1/uploads"
            
            response = requests.post(
                insert_url,
                headers=self.headers,
                json=upload_data,
                timeout=10,
                verify=False
            )
            
            if response.status_code in [200, 201]:
                data = response.json()
                record = data[0] if isinstance(data, list) else data
                return {
                    "success": True,
                    "data": record,
                    "upload_id": record.get("id")
                }
            else:
                error_msg = "Failed to create upload record"
                try:
                    error_data = response.json()
                    error_msg = error_data.get('message', error_msg)
                except:
                    error_msg = f"HTTP {response.status_code}: {response.text}"
                
                return {
                    "success": False,
                    "error": error_msg
                }
        
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def update_upload_status(self, upload_id: str, status: str, error_message: str = None) -> Dict[str, Any]:
        """Update upload status in Supabase database"""
        if not self.client:
            # Mock response for development
            return {"success": True, "data": {"id": upload_id, "status": status}}
        
        try:
            update_data = {
                "status": status,
                "updated_at": datetime.utcnow().isoformat()
            }
            
            if error_message:
                update_data["error_message"] = error_message
            
            if status == "completed":
                update_data["processed_at"] = datetime.utcnow().isoformat()
            
            # Update record using REST API
            update_url = f"{self.url}/rest/v1/uploads?id=eq.{upload_id}"
            
            response = requests.patch(
                update_url,
                headers=self.headers,
                json=update_data,
                timeout=10,
                verify=False
            )
            
            if response.status_code in [200, 204]:
                return {
                    "success": True,
                    "data": update_data
                }
            else:
                error_msg = "Failed to update upload status"
                try:
                    error_data = response.json()
                    error_msg = error_data.get('message', error_msg)
                except:
                    error_msg = f"HTTP {response.status_code}: {response.text}"
                
                return {
                    "success": False,
                    "error": error_msg
                }
        
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_upload_by_id(self, upload_id: str) -> Dict[str, Any]:
        """Get upload record by ID from Supabase database"""
        if not self.client:
            # Mock response for development
            return {
                "success": True,
                "data": {
                    "id": upload_id,
                    "status": "completed",
                    "original_name": "mock_file.pdf",
                    "created_at": datetime.utcnow().isoformat()
                }
            }
        
        try:
            # Get record using REST API
            get_url = f"{self.url}/rest/v1/uploads?id=eq.{upload_id}&select=*"
            
            response = requests.get(
                get_url,
                headers=self.headers,
                timeout=10,
                verify=False
            )
            
            if response.status_code == 200:
                data = response.json()
                if data:
                    return {
                        "success": True,
                        "data": data[0]
                    }
                else:
                    return {
                        "success": False,
                        "error": "Upload not found"
                    }
            else:
                return {
                    "success": False,
                    "error": f"Failed to fetch upload: HTTP {response.status_code}"
                }
        
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def create_content_blocks(self, upload_id: str, blocks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create content blocks in Supabase database"""
        if not self.client:
            # Mock response for development
            return {
                "success": True,
                "data": [{"id": str(uuid.uuid4()), "upload_id": upload_id, **block} for block in blocks]
            }
        
        try:
            # Add upload_id and id to each block
            blocks_with_ids = []
            for block in blocks:
                block_data = {
                    "id": str(uuid.uuid4()),
                    "upload_id": upload_id,
                    **block
                }
                blocks_with_ids.append(block_data)
            
            # Insert blocks using REST API
            insert_url = f"{self.url}/rest/v1/content_blocks"
            
            response = requests.post(
                insert_url,
                headers=self.headers,
                json=blocks_with_ids,
                timeout=10,
                verify=False
            )
            
            if response.status_code in [200, 201]:
                return {
                    "success": True,
                    "data": response.json()
                }
            else:
                error_msg = "Failed to create content blocks"
                try:
                    error_data = response.json()
                    error_msg = error_data.get('message', error_msg)
                except:
                    error_msg = f"HTTP {response.status_code}: {response.text}"
                
                return {
                    "success": False,
                    "error": error_msg
                }
        
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_content_blocks(self, upload_id: str) -> Dict[str, Any]:
        """Get content blocks by upload ID from Supabase database"""
        if not self.client:
            # Mock response for development
            return {
                "success": True,
                "data": [
                    {
                        "id": str(uuid.uuid4()),
                        "upload_id": upload_id,
                        "type": "paragraph",
                        "content": "This is a mock content block from the uploaded file.",
                        "confidence_score": 0.9,
                        "created_at": datetime.utcnow().isoformat()
                    }
                ]
            }
        
        try:
            # Get content blocks using REST API
            get_url = f"{self.url}/rest/v1/content_blocks?upload_id=eq.{upload_id}&select=*&order=created_at"
            
            response = requests.get(
                get_url,
                headers=self.headers,
                timeout=10,
                verify=False
            )
            
            if response.status_code == 200:
                return {
                    "success": True,
                    "data": response.json()
                }
            else:
                return {
                    "success": False,
                    "error": f"Failed to get content blocks: HTTP {response.status_code}"
                }
        
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_all_uploads(self, limit: int = 10) -> Dict[str, Any]:
        """Get all uploads from Supabase database"""
        if not self.client:
            # Mock response for development
            return {
                "success": True,
                "data": [
                    {
                        "id": str(uuid.uuid4()),
                        "original_name": "Sample Playbook 1.pdf",
                        "status": "completed",
                        "created_at": datetime.utcnow().isoformat(),
                        "file_size": 1024000
                    },
                    {
                        "id": str(uuid.uuid4()),
                        "original_name": "Business Strategy Guide.docx",
                        "status": "completed",
                        "created_at": datetime.utcnow().isoformat(),
                        "file_size": 512000
                    }
                ]
            }
        
        try:
            # Get all uploads using REST API
            get_url = f"{self.url}/rest/v1/uploads?select=*&order=created_at.desc&limit={limit}"
            
            response = requests.get(
                get_url,
                headers=self.headers,
                timeout=10,
                verify=False
            )
            
            if response.status_code == 200:
                return {
                    "success": True,
                    "data": response.json()
                }
            else:
                return {
                    "success": False,
                    "error": f"Failed to get uploads: HTTP {response.status_code}"
                }
        
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

# Global Supabase service instance
supabase_service = SupabaseService()
