#!/usr/bin/env python3
"""
Supabase service using only tables from supabase_schema.sql
"""

import os
import uuid
import requests
from datetime import datetime
from typing import Dict, List, Any, Optional
from dotenv import load_dotenv

load_dotenv()

class SupabaseService:
    """Supabase service using only schema-defined tables"""
    
    def __init__(self):
        self.url = os.getenv('SUPABASE_URL')
        self.key = os.getenv('SUPABASE_KEY')
        self.anon_key = self.key  # For compatibility with embedding storage
        self.service_key = os.getenv('SUPABASE_SERVICE_KEY')
        
        if not self.url or not self.key:
            print("⚠️ Supabase credentials not configured")
            self.client = None
        else:
            try:
                self.headers = {
                    'apikey': self.key,
                    'Authorization': f'Bearer {self.key}',
                    'Content-Type': 'application/json',
                    'Accept': 'application/json',
                    'User-Agent': 'playbook-platform/1.0'
                }
                
                # Test connection
                test_response = requests.get(
                    f"{self.url}/rest/v1/",
                    headers=self.headers,
                    timeout=10,
                    verify=False
                )
                
                if test_response.status_code < 400:
                    self.client = "http_client"
                    print("✅ Supabase HTTP client initialized (no WebSocket/realtime)")
                else:
                    print(f"⚠️ Supabase connection failed: {test_response.status_code}")
                    self.client = None
                    
            except Exception as e:
                print(f"⚠️ Failed to initialize Supabase HTTP client: {e}")
                self.client = None

    # USER OPERATIONS
    def create_user(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new user"""
        if not self.client:
            return {"success": False, "error": "Supabase not connected"}
        
        try:
            response = requests.post(
                f"{self.url}/rest/v1/users",
                headers=self.headers,
                json=user_data,
                timeout=10,
                verify=False
            )
            
            if response.status_code in [200, 201]:
                data = response.json()
                user = data[0] if isinstance(data, list) else data
                return {"success": True, "data": user}
            else:
                return {"success": False, "error": f"HTTP {response.status_code}: {response.text}"}
                
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_user_by_id(self, user_id: str) -> Dict[str, Any]:
        """Get user by ID"""
        if not self.client:
            return {"success": False, "error": "Supabase not connected"}
        
        try:
            response = requests.get(
                f"{self.url}/rest/v1/users?id=eq.{user_id}&select=*",
                headers=self.headers,
                timeout=10,
                verify=False
            )
            
            if response.status_code == 200:
                data = response.json()
                if data:
                    return {"success": True, "data": data[0]}
                else:
                    return {"success": False, "error": "User not found"}
            else:
                return {"success": False, "error": f"HTTP {response.status_code}"}
                
        except Exception as e:
            return {"success": False, "error": str(e)}

    # PLAYBOOK OPERATIONS
    def create_playbook(self, playbook_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new playbook"""
        if not self.client:
            return {"success": False, "error": "Supabase not connected"}
        
        try:
            response = requests.post(
                f"{self.url}/rest/v1/playbooks",
                headers=self.headers,
                json=playbook_data,
                timeout=10,
                verify=False
            )
            
            if response.status_code in [200, 201]:
                try:
                    if response.text.strip():
                        data = response.json()
                        if data:
                            playbook = data[0] if isinstance(data, list) else data
                            return {"success": True, "data": playbook}
                    return {"success": True, "data": playbook_data}
                except ValueError as e:
                    print(f"JSON parsing error in create_playbook: {e}")
                    return {"success": True, "data": playbook_data}
            else:
                return {"success": False, "error": f"HTTP {response.status_code}: {response.text}"}
                
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_all_playbooks(self, limit: int = 10) -> Dict[str, Any]:
        """Get all playbooks"""
        if not self.client:
            return {"success": False, "error": "Supabase not connected"}
        
        try:
            response = requests.get(
                f"{self.url}/rest/v1/playbooks?select=*&order=created_at.desc&limit={limit}",
                headers=self.headers,
                timeout=10,
                verify=False
            )
            
            if response.status_code == 200:
                return {"success": True, "data": response.json()}
            else:
                return {"success": False, "error": f"HTTP {response.status_code}"}
                
        except Exception as e:
            return {"success": False, "error": str(e)}

    # PLAYBOOK FILE OPERATIONS (replaces uploads)
    def create_playbook_file(self, file_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a playbook file record"""
        if not self.client:
            return {"success": False, "error": "Supabase not connected"}
        
        try:
            # Ensure ID is set
            if 'id' not in file_data:
                file_data['id'] = str(uuid.uuid4())
                
            response = requests.post(
                f"{self.url}/rest/v1/playbook_files",
                headers=self.headers,
                json=file_data,
                timeout=10,
                verify=False
            )
            
            if response.status_code in [200, 201]:
                # Handle empty response or JSON parsing errors
                try:
                    if response.text.strip():
                        data = response.json()
                        if data:
                            file_record = data[0] if isinstance(data, list) else data
                            return {
                                "success": True,
                                "data": file_record,
                                "upload_id": file_record.get("id")  # For compatibility
                            }
                    
                    # If no data returned, create a mock success response
                    return {
                        "success": True,
                        "data": file_data,
                        "upload_id": file_data.get("id")
                    }
                except ValueError as e:
                    print(f"JSON parsing error: {e}")
                    print(f"Response text: {response.text}")
                    # Return success with original data if JSON parsing fails but status is OK
                    return {
                        "success": True,
                        "data": file_data,
                        "upload_id": file_data.get("id")
                    }
            else:
                return {"success": False, "error": f"HTTP {response.status_code}: {response.text}"}
                
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_playbook_file_by_id(self, file_id: str) -> Dict[str, Any]:
        """Get playbook file by ID"""
        if not self.client:
            return {"success": False, "error": "Supabase not connected"}
        
        try:
            response = requests.get(
                f"{self.url}/rest/v1/playbook_files?id=eq.{file_id}&select=*",
                headers=self.headers,
                timeout=10,
                verify=False
            )
            
            if response.status_code == 200:
                data = response.json()
                if data:
                    return {"success": True, "data": data[0]}
                else:
                    return {"success": False, "error": "File not found"}
            else:
                return {"success": False, "error": f"HTTP {response.status_code}"}
                
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_all_playbook_files(self, limit: int = 10) -> Dict[str, Any]:
        """Get all playbook files"""
        if not self.client:
            return {"success": False, "error": "Supabase not connected"}
        
        try:
            response = requests.get(
                f"{self.url}/rest/v1/playbook_files?select=*&order=created_at.desc&limit={limit}",
                headers=self.headers,
                timeout=10,
                verify=False
            )
            
            if response.status_code == 200:
                return {"success": True, "data": response.json()}
            else:
                return {"success": False, "error": f"HTTP {response.status_code}"}
                
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_files_by_playbook(self, playbook_id: str) -> Dict[str, Any]:
        """Get all files for a specific playbook"""
        if not self.client:
            return {"success": False, "error": "Supabase not connected"}
        
        try:
            response = requests.get(
                f"{self.url}/rest/v1/playbook_files?playbook_id=eq.{playbook_id}&select=*&order=created_at.desc",
                headers=self.headers,
                timeout=10,
                verify=False
            )
            
            if response.status_code == 200:
                return {"success": True, "data": response.json()}
            else:
                return {"success": False, "error": f"HTTP {response.status_code}"}
                
        except Exception as e:
            return {"success": False, "error": str(e)}

    # COMPATIBILITY METHODS (to avoid breaking existing code)
    def create_upload_record(self, upload_data: Dict[str, Any]) -> Dict[str, Any]:
        """Compatibility method - creates playbook file record"""
        # Map upload data to playbook_files structure
        file_data = {
            "file_name": upload_data.get("original_name", "unknown"),
            "file_type": self._get_file_type(upload_data.get("original_name", "")),
            "storage_path": upload_data.get("storage_path", ""),
            "uploaded_by": upload_data.get("uploaded_by"),
            "playbook_id": upload_data.get("playbook_id")  # Must be provided
        }
        
        if not file_data["playbook_id"]:
            return {"success": False, "error": "playbook_id is required"}
            
        return self.create_playbook_file(file_data)

    def update_upload_status(self, file_id: str, status: str, error_message: str = None) -> Dict[str, Any]:
        """Compatibility method - playbook_files don't have status, so this is a no-op"""
        return {"success": True, "data": {"id": file_id, "message": "Status update not applicable to playbook_files"}}

    def get_upload_by_id(self, file_id: str) -> Dict[str, Any]:
        """Compatibility method - gets playbook file by ID"""
        return self.get_playbook_file_by_id(file_id)

    def get_all_uploads(self, limit: int = 10) -> Dict[str, Any]:
        """Compatibility method - gets all playbook files"""
        return self.get_all_playbook_files(limit)

    def create_content_blocks(self, file_id: str, blocks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Compatibility method - content blocks are not in schema, so this is a no-op"""
        return {"success": True, "data": [{"id": str(uuid.uuid4()), "file_id": file_id, **block} for block in blocks]}
    
    def store_embeddings(self, file_id: str, blocks_with_embeddings: list):
        """Store embeddings in the embeddings table"""
        print(f"💾 Storing {len(blocks_with_embeddings)} embeddings for file {file_id}")
        
        success_count = 0
        for i, block in enumerate(blocks_with_embeddings):
            try:
                embedding_data = {
                    "file_id": file_id,
                    "chunk_index": i,
                    "content": block.get("content", "")[:1000],  # Limit content length
                    "embedding": block.get("embedding", []),
                    "type": "playbook"
                }
                
                headers = {
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self.service_key}",
                    "apikey": self.anon_key,
                    "Prefer": "return=minimal"
                }
                
                response = requests.post(
                    f"{self.url}/rest/v1/embeddings",
                    json=embedding_data,
                    headers=headers,
                    verify=False
                )
                
                if response.status_code in [200, 201]:
                    success_count += 1
                else:
                    print(f"❌ Failed to store embedding {i}: {response.status_code} - {response.text}")
                    
            except Exception as e:
                print(f"❌ Error storing embedding {i}: {e}")
        
        print(f"✅ Stored {success_count}/{len(blocks_with_embeddings)} embeddings")
        return {"success": True, "stored": success_count}
    
    def update_playbook_tags(self, playbook_id: str, tags: list):
        """Update playbook with extracted tags"""
        try:
            update_data = {
                "tags": tags,
                "description": f"Auto-generated from file upload with {len(tags)} tags"
            }
            
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.service_key}",
                "apikey": self.anon_key,
                "Prefer": "return=minimal"
            }
            
            response = requests.patch(
                f"{self.url}/rest/v1/playbooks?id=eq.{playbook_id}",
                json=update_data,
                headers=headers,
                verify=False
            )
            
            if response.status_code in [200, 204]:
                print(f"✅ Updated playbook {playbook_id} with {len(tags)} tags")
                return {"success": True}
            else:
                print(f"❌ Failed to update playbook tags: {response.status_code} - {response.text}")
                return {"success": False, "error": response.text}
                
        except Exception as e:
            print(f"❌ Error updating playbook tags: {e}")
            return {"success": False, "error": str(e)}

    def get_content_blocks(self, file_id: str) -> Dict[str, Any]:
        """Compatibility method - returns empty blocks since not in schema"""
        return {"success": True, "data": []}

    def upload_file(self, file_path: str, file_name: str, bucket_name: str = "playbooks") -> Dict[str, Any]:
        """Mock file upload - returns mock data"""
        return {
            "success": True,
            "public_url": f"mock://storage/{bucket_name}/{file_name}",
            "path": f"{bucket_name}/{file_name}"
        }

    def _get_file_type(self, filename: str) -> str:
        """Extract file type from filename"""
        if '.' not in filename:
            return 'txt'
        
        ext = filename.rsplit('.', 1)[1].lower()
        # Map to allowed types in schema
        allowed_types = {'md', 'pdf', 'csv', 'docx', 'txt'}
        return ext if ext in allowed_types else 'txt'

# Global service instance
supabase_service = SupabaseService()
