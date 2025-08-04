#!/usr/bin/env python3
"""
Direct database test - Insert data directly into Supabase
"""
import os
import requests
import json
import uuid
from datetime import datetime
from dotenv import load_dotenv
import urllib3

# Disable SSL warnings for testing
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Load environment variables
load_dotenv()

def direct_insert_test():
    """Test direct insertion into Supabase uploads table"""
    
    url = os.getenv('SUPABASE_URL')
    service_key = os.getenv('SUPABASE_SERVICE_KEY')
    
    print("🔧 Direct Database Insert Test")
    print(f"URL: {url}")
    print(f"Service Key: {service_key[:20]}...{service_key[-10:] if service_key else 'None'}")
    print("-" * 50)
    
    if not url or not service_key:
        print("❌ Missing Supabase credentials")
        return False
        
    # Prepare test data
    test_data = {
        "id": str(uuid.uuid4()),
        "filename": f"test_upload_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
        "original_name": "test_file.txt",
        "file_path": "/uploads/test_file.txt",
        "file_size": 1024,
        "mime_type": "text/plain",
        "source_url": None,
        "status": "uploaded",
        "error_message": None,
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
        "processed_at": None
    }
    
    # Insert data
    headers = {
        'apikey': service_key,
        'Authorization': f'Bearer {service_key}',
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }
    
    insert_url = f"{url}/rest/v1/uploads"
    
    try:
        print("📤 Inserting test data...")
        response = requests.post(insert_url, headers=headers, json=test_data, verify=False)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 201:
            print("✅ Data inserted successfully!")
            print(f"Inserted record ID: {test_data['id']}")
            return True
        else:
            print(f"❌ Insert failed: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error during insert: {e}")
        return False

def verify_insert():
    """Verify the inserted data exists"""
    
    url = os.getenv('SUPABASE_URL')
    service_key = os.getenv('SUPABASE_SERVICE_KEY')
    
    headers = {
        'apikey': service_key,
        'Authorization': f'Bearer {service_key}',
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }
    
    # Get all records to verify
    select_url = f"{url}/rest/v1/uploads?select=*"
    
    try:
        print("\n📥 Verifying inserted data...")
        response = requests.get(select_url, headers=headers, verify=False)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Found {len(data)} records in uploads table")
            
            for record in data:
                print(f"   - ID: {record.get('id')}")
                print(f"   - Filename: {record.get('filename')}")
                print(f"   - Status: {record.get('status')}")
                print(f"   - Created: {record.get('created_at')}")
                print()
                
            return True
        else:
            print(f"❌ Verification failed: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error during verification: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Starting Direct Database Test")
    print("=" * 50)
    
    # Test direct insert
    insert_success = direct_insert_test()
    
    if insert_success:
        # Verify the insert
        verify_insert()
    
    print("\n" + "=" * 50)
    print("Direct Database Test Complete")