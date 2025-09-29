#!/usr/bin/env python3
"""
Startup script for the CSI Hackathon application
"""

import os
import sys
import subprocess
from pathlib import Path

def check_requirements():
    """Check if required files and directories exist"""
    required_files = [
        'app.py',
        'database.py',
        'requirements.txt'
    ]
    
    required_dirs = [
        'frontend',
        'data',
        'uploads'
    ]
    
    missing_files = [f for f in required_files if not Path(f).exists()]
    missing_dirs = [d for d in required_dirs if not Path(d).exists()]
    
    if missing_files:
        print(f"❌ Missing required files: {', '.join(missing_files)}")
        return False
    
    if missing_dirs:
        print(f"❌ Missing required directories: {', '.join(missing_dirs)}")
        return False
    
    return True

def setup_environment():
    """Set up the environment"""
    print("🔧 Setting up environment...")
    
    # Create required directories
    Path('data').mkdir(exist_ok=True)
    Path('uploads').mkdir(exist_ok=True)
    Path('uploads/pdfs').mkdir(exist_ok=True)
    Path('uploads/audio').mkdir(exist_ok=True)
    
    print("✅ Environment setup complete")

def install_dependencies():
    """Install Python dependencies"""
    print("📦 Installing Python dependencies...")
    
    try:
        subprocess.run([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'], 
                      check=True, capture_output=True)
        print("✅ Python dependencies installed")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install Python dependencies: {e}")
        return False

def check_frontend():
    """Check if frontend dependencies are installed"""
    frontend_dir = Path('frontend')
    node_modules = frontend_dir / 'node_modules'
    
    if not node_modules.exists():
        print("📦 Frontend dependencies not found. Please run:")
        print("   cd frontend && npm install")
        return False
    
    return True

def start_backend():
    """Start the Flask backend"""
    print("🚀 Starting Flask backend...")
    
    try:
        # Set environment variables
        env = os.environ.copy()
        env['FLASK_APP'] = 'app.py'
        env['FLASK_ENV'] = 'development'
        
        subprocess.run([sys.executable, 'app.py'], env=env)
    except KeyboardInterrupt:
        print("\n🛑 Backend stopped")
    except Exception as e:
        print(f"❌ Error starting backend: {e}")

def main():
    """Main startup function"""
    print("🎯 CSI Hackathon Platform Startup")
    print("=" * 40)
    
    # Check requirements
    if not check_requirements():
        print("❌ Setup incomplete. Please ensure all required files are present.")
        return
    
    # Setup environment
    setup_environment()
    
    # Install dependencies
    if not install_dependencies():
        return
    
    # Check frontend
    if not check_frontend():
        print("⚠️  Frontend not ready. Backend will start without frontend.")
        print("   To start frontend separately, run: cd frontend && npm start")
    
    print("\n🎉 Setup complete! Starting application...")
    print("📱 Frontend: http://localhost:3000")
    print("🔧 Backend API: http://localhost:5000")
    print("🛑 Press Ctrl+C to stop")
    print("=" * 40)
    
    # Start backend
    start_backend()

if __name__ == '__main__':
    main()
