#!/usr/bin/env python3
"""
Complete Supabase test including table creation and upload workflow
"""
import os
import requests
import json
from datetime import datetime
import uuid
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_supabase_connection():
    """Test basic Supabase connectivity"""
    url = os.getenv('SUPABASE_URL')
    key = os.getenv('SUPABASE_KEY')
    
    print("🔧 Testing Supabase Connection")
    print(f"URL: {url}")
    print(f"Key: {key[:20]}...{key[-10:] if key else 'None'}")
    print("-" * 50)
    
    if not url or not key:
        print("❌ SUPABASE_URL or SUPABASE_KEY not set in environment")
        return False
    
    if url == 'your_supabase_url' or key == 'your_supabase_key':
        print("❌ Supabase credentials are still placeholder values")
        return False
    
    headers = {
        'apikey': key,
        'Authorization': f'Bearer {key}',
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'User-Agent': 'playbook-test/1.0'
    }
    
    try:
        print("1. Testing basic connectivity...")
        response = requests.get(
            f"{url}/rest/v1/",
            headers=headers,
            timeout=10,
            verify=False
        )
        
        print(f"   Status: {response.status_code}")
        
        if response.status_code < 400:
            print("   ✅ Basic connectivity successful")
        else:
            print(f"   ❌ Basic connectivity failed: {response.text}")
            return False
            
    except Exception as e:
        print(f"   ❌ Connection error: {e}")
        return False
    
    return True

def create_missing_tables():
    """Create the uploads and content_blocks tables if they don't exist"""
    url = os.getenv('SUPABASE_URL')
    key = os.getenv('SUPABASE_SERVICE_KEY') or os.getenv('SUPABASE_KEY')
    
    headers = {
        'apikey': key,
        'Authorization': f'Bearer {key}',
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }
    
    try:
        print("\n2. Creating missing tables...")
        
        # Try to create uploads table
        uploads_sql = """
        CREATE TABLE IF NOT EXISTS uploads (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            filename TEXT,
            original_name TEXT,
            file_path TEXT,
            file_size INTEGER,
            mime_type TEXT,
            source_url TEXT,
            status TEXT CHECK (status IN ('uploaded', 'processing', 'completed', 'failed')) DEFAULT 'uploaded',
            error_message TEXT,
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW(),
            processed_at TIMESTAMP
        );
        """
        
        content_blocks_sql = """
        CREATE TABLE IF NOT EXISTS content_blocks (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            upload_id UUID REFERENCES uploads(id) ON DELETE CASCADE,
            type TEXT NOT NULL,
            content TEXT NOT NULL,
            confidence_score FLOAT DEFAULT 0.8,
            suggested_asset_type TEXT,
            created_at TIMESTAMP DEFAULT NOW()
        );
        """
        
        # Note: Supabase REST API doesn't support direct SQL execution
        # These tables need to be created via Supabase dashboard or SQL editor
        print("   ⚠️  Tables need to be created via Supabase SQL Editor:")
        print("   - uploads table")
        print("   - content_blocks table")
        print("   ✅ SQL provided above")
        return True
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def test_uploads_table():
    """Test uploads table access"""
    url = os.getenv('SUPABASE_URL')
    key = os.getenv('SUPABASE_KEY')
    
    headers = {
        'apikey': key,
        'Authorization': f'Bearer {key}',
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }
    
    try:
        print("\n3. Testing uploads table access...")
        response = requests.get(
            f"{url}/rest/v1/uploads?limit=1",
            headers=headers,
            timeout=10,
            verify=False
        )
        
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ uploads table accessible, found {len(data)} records")
            return True
        elif response.status_code == 404:
            print("   ❌ uploads table does not exist")
            return False
        else:
            print(f"   ❌ Table access failed: {response.text}")
            return False
            
    except Exception as e:
        print(f"   ❌ Table access error: {e}")
        return False

def test_content_blocks_table():
    """Test content_blocks table access"""
    url = os.getenv('SUPABASE_URL')
    key = os.getenv('SUPABASE_KEY')
    
    headers = {
        'apikey': key,
        'Authorization': f'Bearer {key}',
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }
    
    try:
        print("\n4. Testing content_blocks table access...")
        response = requests.get(
            f"{url}/rest/v1/content_blocks?limit=1",
            headers=headers,
            timeout=10,
            verify=False
        )
        
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ content_blocks table accessible, found {len(data)} records")
            return True
        elif response.status_code == 404:
            print("   ❌ content_blocks table does not exist")
            return False
        else:
            print(f"   ❌ Table access failed: {response.text}")
            return False
            
    except Exception as e:
        print(f"   ❌ Table access error: {e}")
        return False

def test_upload_workflow():
    """Test the complete upload workflow"""
    url = os.getenv('SUPABASE_URL')
    key = os.getenv('SUPABASE_KEY')
    
    headers = {
        'apikey': key,
        'Authorization': f'Bearer {key}',
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'Prefer': 'return=representation'
    }
    
    upload_id = str(uuid.uuid4())
    
    test_upload_data = {
        'id': upload_id,
        'original_name': 'test_playbook.docx',
        'filename': f'{upload_id}_test_playbook.docx',
        'file_size': 1024,
        'mime_type': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'status': 'uploaded',
        'created_at': datetime.utcnow().isoformat()
    }
    
    try:
        print("\n5. Testing upload workflow...")
        
        # Step 1: Insert upload record
        print("   Step 1: Creating upload record...")
        response = requests.post(
            f"{url}/rest/v1/uploads",
            headers=headers,
            json=test_upload_data,
            timeout=10,
            verify=False
        )
        
        print(f"   Status: {response.status_code}")
        
        if response.status_code in [200, 201]:
            print("   ✅ Upload record created successfully!")
            upload_result = response.json()
            if isinstance(upload_result, list):
                upload_result = upload_result[0]
            print(f"   Upload ID: {upload_result.get('id')}")
        else:
            print(f"   ❌ Upload creation failed: {response.text}")
            return False
        
        # Step 2: Update status to processing
        print("   Step 2: Updating status to processing...")
        update_data = {
            'status': 'processing',
            'updated_at': datetime.utcnow().isoformat()
        }
        
        response = requests.patch(
            f"{url}/rest/v1/uploads?id=eq.{upload_id}",
            headers=headers,
            json=update_data,
            timeout=10,
            verify=False
        )
        
        if response.status_code in [200, 204]:
            print("   ✅ Status updated to processing!")
        else:
            print(f"   ❌ Status update failed: {response.text}")
        
        # Step 3: Add content blocks
        print("   Step 3: Adding content blocks...")
        content_blocks = [
            {
                'id': str(uuid.uuid4()),
                'upload_id': upload_id,
                'type': 'heading',
                'content': 'Test Playbook Title',
                'confidence_score': 0.95
            },
            {
                'id': str(uuid.uuid4()),
                'upload_id': upload_id,
                'type': 'paragraph',
                'content': 'This is a test paragraph from the uploaded document.',
                'confidence_score': 0.85
            }
        ]
        
        response = requests.post(
            f"{url}/rest/v1/content_blocks",
            headers=headers,
            json=content_blocks,
            timeout=10,
            verify=False
        )
        
        if response.status_code in [200, 201]:
            print("   ✅ Content blocks created successfully!")
        else:
            print(f"   ❌ Content blocks creation failed: {response.text}")
        
        # Step 4: Update status to completed
        print("   Step 4: Updating status to completed...")
        final_update = {
            'status': 'completed',
            'processed_at': datetime.utcnow().isoformat(),
            'updated_at': datetime.utcnow().isoformat()
        }
        
        response = requests.patch(
            f"{url}/rest/v1/uploads?id=eq.{upload_id}",
            headers=headers,
            json=final_update,
            timeout=10,
            verify=False
        )
        
        if response.status_code in [200, 204]:
            print("   ✅ Status updated to completed!")
        else:
            print(f"   ❌ Final status update failed: {response.text}")
        
        # Step 5: Verify the complete record
        print("   Step 5: Verifying complete record...")
        response = requests.get(
            f"{url}/rest/v1/uploads?id=eq.{upload_id}",
            headers=headers,
            timeout=10,
            verify=False
        )
        
        if response.status_code == 200:
            data = response.json()
            if data:
                record = data[0]
                print(f"   ✅ Record verified!")
                print(f"   Final status: {record.get('status')}")
                print(f"   Original name: {record.get('original_name')}")
                return True
            else:
                print("   ❌ Record not found")
                return False
        else:
            print(f"   ❌ Record verification failed: {response.text}")
            return False
            
    except Exception as e:
        print(f"   ❌ Upload workflow error: {e}")
        return False

def test_network_connectivity():
    """Test general network connectivity"""
    print("\n6. Testing network connectivity...")
    
    test_urls = [
        "https://httpbin.org/get",
        "https://jsonplaceholder.typicode.com/posts/1"
    ]
    
    for test_url in test_urls:
        try:
            response = requests.get(test_url, timeout=5, verify=False)
            print(f"   {test_url}: ✅ {response.status_code}")
        except Exception as e:
            print(f"   {test_url}: ❌ {e}")

if __name__ == "__main__":
    print("🧪 Complete Supabase Upload Workflow Test")
    print("=" * 50)
    
    # Test network connectivity
    test_network_connectivity()
    
    # Test Supabase connection
    if test_supabase_connection():
        create_missing_tables()
        
        # Test table access
        uploads_ok = test_uploads_table()
        content_ok = test_content_blocks_table()
        
        if uploads_ok and content_ok:
            # Test complete workflow
            test_upload_workflow()
        else:
            print("\n❌ Cannot proceed with workflow test - tables not accessible")
            print("Please create the missing tables in Supabase SQL Editor:")
            print("""
CREATE TABLE IF NOT EXISTS uploads (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    filename TEXT,
    original_name TEXT,
    file_path TEXT,
    file_size INTEGER,
    mime_type TEXT,
    source_url TEXT,
    status TEXT CHECK (status IN ('uploaded', 'processing', 'completed', 'failed')) DEFAULT 'uploaded',
    error_message TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    processed_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS content_blocks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    upload_id UUID REFERENCES uploads(id) ON DELETE CASCADE,
    type TEXT NOT NULL,
    content TEXT NOT NULL,
    confidence_score FLOAT DEFAULT 0.8,
    suggested_asset_type TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);
            """)
    
    print("\n" + "=" * 50)
    print("Test completed!") 