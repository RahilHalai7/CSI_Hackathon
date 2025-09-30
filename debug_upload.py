#!/usr/bin/env python3
"""
Debug script to test file upload and processing
"""

import os
import sys
import requests
import json
from pathlib import Path

def test_upload():
    """Test file upload to the API"""
    
    # Check if we have test files
    test_files = []
    
    # Look for PDF files
    pdf_dir = Path('pdf')
    if pdf_dir.exists():
        test_files.extend(list(pdf_dir.glob('*.pdf')))
    
    # Look for audio files
    audio_dir = Path('audio')
    if audio_dir.exists():
        test_files.extend(list(audio_dir.glob('*.*')))
    
    if not test_files:
        print("❌ No test files found in pdf/ or audio/ directories")
        return False
    
    test_file = test_files[0]
    print(f"📁 Testing upload with: {test_file}")
    
    # Test file upload
    url = 'http://localhost:5000/api/entrepreneur/submit'
    
    # You'll need to replace this with actual authentication
    headers = {
        'Authorization': 'Bearer 1'  # Replace with actual user ID token
    }
    
    try:
        with open(test_file, 'rb') as f:
            files = {'file': (test_file.name, f, 'application/octet-stream')}
            data = {
                'title': f'Test upload of {test_file.name}',
                'description': 'This is a test upload to debug processing issues'
            }
            
            print(f"📤 Uploading to: {url}")
            response = requests.post(url, headers=headers, files=files, data=data, timeout=300)
            
            print(f"Status Code: {response.status_code}")
            print(f"Response: {response.text}")
            
            if response.status_code == 200:
                result = response.json()
                print("✅ Upload successful!")
                print(f"Submission ID: {result.get('submission_id')}")
                return True
            else:
                print("❌ Upload failed")
                return False
                
    except requests.exceptions.RequestException as e:
        print(f"❌ Request error: {e}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def check_api_status():
    """Check if the API is running"""
    try:
        response = requests.get('http://localhost:5000/api/me', timeout=5)
        print(f"API Status: {response.status_code}")
        return response.status_code == 401  # 401 is expected without auth
    except requests.exceptions.RequestException:
        print("❌ API is not running")
        return False

def main():
    print("🔍 CSI Hackathon Upload Debug")
    print("=" * 40)
    
    # Check if API is running
    if not check_api_status():
        print("❌ Please start the Flask app first: python app.py")
        return
    
    print("✅ API is running")
    
    # Test upload
    success = test_upload()
    
    if success:
        print("\n✅ Upload test completed successfully")
    else:
        print("\n❌ Upload test failed")
        print("\n💡 Troubleshooting:")
        print("1. Make sure you're logged in as an entrepreneur")
        print("2. Check the browser console for errors")
        print("3. Check the Flask app logs for processing errors")
        print("4. Run test_processing.py to check individual components")

if __name__ == '__main__':
    main()
