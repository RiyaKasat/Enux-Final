#!/usr/bin/env python3
"""
Test Supabase connectivity and data insertion
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
        # Test basic connectivity
        print("1. Testing basic connectivity...")
        response = requests.get(
            f"{url}/rest/v1/",
            headers=headers,
            timeout=10,
            verify=False  # Disable SSL verification for corporate networks
        )
        
        print(f"   Status: {response.status_code}")
        print(f"   Headers: {dict(response.headers)}")
        
        if response.status_code < 400:
            print("   ✅ Basic connectivity successful")
        else:
            print(f"   ❌ Basic connectivity failed: {response.text}")
            return False
            
    except Exception as e:
        print(f"   ❌ Connection error: {e}")
        return False
    
    return True

def test_table_access():
    """Test table access (uploads table)"""
    url = os.getenv('SUPABASE_URL')
    key = os.getenv('SUPABASE_KEY')
    
    headers = {
        'apikey': key,
        'Authorization': f'Bearer {key}',
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }
    
    try:
        print("\n2. Testing uploads table access...")
        response = requests.get(
            f"{url}/rest/v1/uploads?limit=1",
            headers=headers,
            timeout=10,
            verify=False
        )
        
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Table access successful, found {len(data)} records")
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

def test_data_insertion():
    """Test inserting a test record"""
    url = os.getenv('SUPABASE_URL')
    key = os.getenv('SUPABASE_KEY')
    
    headers = {
        'apikey': key,
        'Authorization': f'Bearer {key}',
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'Prefer': 'return=representation'
    }
    
    test_data = {
        'id': str(uuid.uuid4()),
        'original_name': 'test_upload.txt',
        'file_size': 1024,
        'mime_type': 'text/plain',
        'status': 'completed',
        'created_at': datetime.utcnow().isoformat(),
        'source_type': 'test'
    }
    
    try:
        print("\n3. Testing data insertion...")
        response = requests.post(
            f"{url}/rest/v1/uploads",
            headers=headers,
            json=test_data,
            timeout=10,
            verify=False
        )
        
        print(f"   Status: {response.status_code}")
        
        if response.status_code in [200, 201]:
            result = response.json()
            print(f"   ✅ Data insertion successful!")
            print(f"   Record ID: {result[0]['id'] if isinstance(result, list) else result.get('id')}")
            return True
        else:
            print(f"   ❌ Data insertion failed: {response.text}")
            return False
            
    except Exception as e:
        print(f"   ❌ Data insertion error: {e}")
        return False

def test_network_connectivity():
    """Test general network connectivity"""
    print("\n4. Testing network connectivity...")
    
    test_urls = [
        "https://httpbin.org/get",
        "https://jsonplaceholder.typicode.com/posts/1",
        "https://api.github.com"
    ]
    
    for test_url in test_urls:
        try:
            response = requests.get(test_url, timeout=5, verify=False)
            print(f"   {test_url}: ✅ {response.status_code}")
        except Exception as e:
            print(f"   {test_url}: ❌ {e}")

if __name__ == "__main__":
    print("🧪 Supabase Connectivity Test")
    print("=" * 50)
    
    # Test network connectivity first
    test_network_connectivity()
    
    # Test Supabase connection
    if test_supabase_connection():
        test_table_access()
        test_data_insertion()
    
    print("\n" + "=" * 50)
    print("Test completed!") 