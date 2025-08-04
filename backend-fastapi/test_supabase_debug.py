#!/usr/bin/env python3

import os
import requests
from dotenv import load_dotenv

load_dotenv()

def test_supabase_debug():
    """Debug Supabase connection with detailed logging"""
    
    url = os.getenv('SUPABASE_URL')
    anon_key = os.getenv('SUPABASE_KEY')
    service_key = os.getenv('SUPABASE_SERVICE_KEY')
    
    print("🔧 Debugging Supabase Connection")
    print(f"URL: {url}")
    print(f"Anon Key: {anon_key[:20]}...{anon_key[-10:] if anon_key else 'None'}")
    print(f"Service Key: {service_key[:20]}...{service_key[-10:] if service_key else 'None'}")
    print("-" * 50)
    
    # Test which key the backend logic would use
    auth_key = service_key if service_key else anon_key
    print(f"✅ Backend will use: {'SERVICE_KEY' if service_key else 'ANON_KEY'}")
    print(f"Auth Key: {auth_key[:20]}...{auth_key[-10:] if auth_key else 'None'}")
    print("-" * 50)
    
    # Test connection with the auth key
    headers = {
        'apikey': auth_key,
        'Authorization': f'Bearer {auth_key}',
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'User-Agent': 'playbook-platform/1.0'
    }
    
    try:
        print("🔍 Testing basic connection...")
        response = requests.get(
            f"{url}/rest/v1/",
            headers=headers,
            timeout=10,
            verify=False
        )
        print(f"Basic connection: {response.status_code}")
        
        print("🔍 Testing uploads table access...")
        response = requests.get(
            f"{url}/rest/v1/uploads",
            headers=headers,
            timeout=10,
            verify=False
        )
        print(f"Uploads table access: {response.status_code}")
        
        if response.status_code != 200:
            print(f"❌ Error: {response.text}")
        else:
            print("✅ Uploads table accessible!")
            
        print("🔍 Testing insert permissions...")
        test_data = {
            "filename": "test_debug.txt",
            "original_name": "test_debug.txt",
            "file_size": 100,
            "mime_type": "text/plain",
            "status": "uploaded"
        }
        
        response = requests.post(
            f"{url}/rest/v1/uploads",
            headers=headers,
            json=test_data,
            timeout=10,
            verify=False
        )
        print(f"Insert test: {response.status_code}")
        
        if response.status_code != 201:
            print(f"❌ Insert Error: {response.text}")
        else:
            print("✅ Insert successful!")
            
    except Exception as e:
        print(f"❌ Connection error: {e}")

if __name__ == "__main__":
    test_supabase_debug() 