#!/usr/bin/env python3
"""
Test script to debug file processing issues
"""

import os
import sys
import subprocess
import tempfile
from pathlib import Path

def test_pdf_processing():
    """Test PDF processing"""
    print("🔍 Testing PDF processing...")
    
    # Check if pdf_to_txt.py exists
    if not os.path.exists('pdf_to_txt.py'):
        print("❌ pdf_to_txt.py not found")
        return False
    
    # Check if there are any PDF files in the pdf/ directory
    pdf_dir = Path('pdf')
    if not pdf_dir.exists():
        print("❌ pdf/ directory not found")
        return False
    
    pdf_files = list(pdf_dir.glob('*.pdf'))
    if not pdf_files:
        print("❌ No PDF files found in pdf/ directory")
        return False
    
    test_pdf = pdf_files[0]
    print(f"📄 Testing with: {test_pdf}")
    
    try:
        # Test the PDF processing command
        cmd = [
            sys.executable, 'pdf_to_txt.py',
            '--pdf', str(test_pdf),
            '--output', 'test_output.txt',
            '--save-to-db',
            '--db-path', 'data/ocr.db'
        ]
        
        print(f"Running: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        
        print(f"Return code: {result.returncode}")
        print(f"STDOUT: {result.stdout}")
        print(f"STDERR: {result.stderr}")
        
        if result.returncode == 0:
            print("✅ PDF processing successful")
            if os.path.exists('test_output.txt'):
                with open('test_output.txt', 'r', encoding='utf-8') as f:
                    content = f.read()
                print(f"Output length: {len(content)} characters")
                print(f"First 200 chars: {content[:200]}...")
                os.remove('test_output.txt')
            return True
        else:
            print("❌ PDF processing failed")
            return False
            
    except subprocess.TimeoutExpired:
        print("❌ PDF processing timed out")
        return False
    except Exception as e:
        print(f"❌ PDF processing error: {e}")
        return False

def test_audio_processing():
    """Test audio processing"""
    print("\n🔍 Testing audio processing...")
    
    # Check if asr.py exists
    if not os.path.exists('asr.py'):
        print("❌ asr.py not found")
        return False
    
    # Check if there are any audio files in the audio/ directory
    audio_dir = Path('audio')
    if not audio_dir.exists():
        print("❌ audio/ directory not found")
        return False
    
    audio_files = list(audio_dir.glob('*.*'))
    if not audio_files:
        print("❌ No audio files found in audio/ directory")
        return False
    
    test_audio = audio_files[0]
    print(f"🎵 Testing with: {test_audio}")
    
    try:
        # Test the audio processing command
        cmd = [
            sys.executable, 'asr.py',
            '--input', str(test_audio),
            '--output', 'test_audio_output.txt'
        ]
        
        print(f"Running: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        
        print(f"Return code: {result.returncode}")
        print(f"STDOUT: {result.stdout}")
        print(f"STDERR: {result.stderr}")
        
        if result.returncode == 0:
            print("✅ Audio processing successful")
            if os.path.exists('test_audio_output.txt'):
                with open('test_audio_output.txt', 'r', encoding='utf-8') as f:
                    content = f.read()
                print(f"Output length: {len(content)} characters")
                print(f"First 200 chars: {content[:200]}...")
                os.remove('test_audio_output.txt')
            return True
        else:
            print("❌ Audio processing failed")
            return False
            
    except subprocess.TimeoutExpired:
        print("❌ Audio processing timed out")
        return False
    except Exception as e:
        print(f"❌ Audio processing error: {e}")
        return False

def test_bmc_generation():
    """Test BMC generation"""
    print("\n🔍 Testing BMC generation...")
    
    # Check if bmc.py exists
    if not os.path.exists('bmc.py'):
        print("❌ bmc.py not found")
        return False
    
    try:
        # Create a test text file
        test_text = "This is a test business idea for a mobile app that helps people find local restaurants."
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
            f.write(test_text)
            temp_text_file = f.name
        
        # Test BMC generation
        cmd = [
            sys.executable, 'bmc.py', 'image',
            '--output', 'test_bmc.png',
            '--title', 'Test Business Model Canvas',
            '--data-file', temp_text_file
        ]
        
        print(f"Running: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        
        print(f"Return code: {result.returncode}")
        print(f"STDOUT: {result.stdout}")
        print(f"STDERR: {result.stderr}")
        
        # Clean up
        os.unlink(temp_text_file)
        
        if result.returncode == 0:
            print("✅ BMC generation successful")
            if os.path.exists('test_bmc.png'):
                print("✅ BMC image created")
                os.remove('test_bmc.png')
            return True
        else:
            print("❌ BMC generation failed")
            return False
            
    except Exception as e:
        print(f"❌ BMC generation error: {e}")
        return False

def check_environment():
    """Check environment setup"""
    print("🔍 Checking environment...")
    
    # Check Python version
    print(f"Python version: {sys.version}")
    
    # Check if required directories exist
    required_dirs = ['data', 'uploads', 'uploads/pdfs', 'uploads/audio']
    for dir_path in required_dirs:
        if os.path.exists(dir_path):
            print(f"✅ {dir_path} exists")
        else:
            print(f"❌ {dir_path} missing")
            os.makedirs(dir_path, exist_ok=True)
            print(f"✅ Created {dir_path}")
    
    # Check if database exists
    if os.path.exists('data/app.db'):
        print("✅ Database exists")
    else:
        print("❌ Database missing - run the app once to create it")
    
    # Check environment variables
    env_vars = ['GOOGLE_APPLICATION_CREDENTIALS', 'GEMINI_API_KEY']
    for var in env_vars:
        if os.getenv(var):
            print(f"✅ {var} is set")
        else:
            print(f"⚠️  {var} is not set")

def main():
    print("🧪 CSI Hackathon File Processing Test")
    print("=" * 50)
    
    # Check environment
    check_environment()
    
    # Test processing
    pdf_ok = test_pdf_processing()
    audio_ok = test_audio_processing()
    bmc_ok = test_bmc_generation()
    
    print("\n📊 Test Results:")
    print(f"PDF Processing: {'✅ PASS' if pdf_ok else '❌ FAIL'}")
    print(f"Audio Processing: {'✅ PASS' if audio_ok else '❌ FAIL'}")
    print(f"BMC Generation: {'✅ PASS' if bmc_ok else '❌ FAIL'}")
    
    if not (pdf_ok or audio_ok):
        print("\n💡 Troubleshooting Tips:")
        print("1. Make sure all required Python packages are installed: pip install -r requirements.txt")
        print("2. Check if Google Cloud credentials are properly set up")
        print("3. Verify that GEMINI_API_KEY is set in your environment")
        print("4. Ensure the processing scripts (pdf_to_txt.py, asr.py, bmc.py) are in the project root")

if __name__ == '__main__':
    main()
