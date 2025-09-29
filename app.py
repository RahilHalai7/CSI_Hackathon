"""
Flask API for CSI Hackathon application
"""

import os
import json
import uuid
import sqlite3
from datetime import datetime
from pathlib import Path
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from werkzeug.utils import secure_filename
import subprocess
import tempfile
import shutil

from database import db

app = Flask(__name__)
CORS(app)

# Configuration
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'pdf', 'mp3', 'wav', 'm4a', 'mp4'}
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE

# Create upload directories
Path(UPLOAD_FOLDER).mkdir(exist_ok=True)
Path(UPLOAD_FOLDER, 'pdfs').mkdir(exist_ok=True)
Path(UPLOAD_FOLDER, 'audio').mkdir(exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def process_pdf_file(file_path):
    """Process PDF file using the existing pdf_to_txt.py script"""
    try:
        # Create a temporary directory for processing
        with tempfile.TemporaryDirectory() as temp_dir:
            output_file = os.path.join(temp_dir, 'output.txt')
            
            # Run the PDF processing script
            cmd = [
                'python', 'pdf_to_txt.py',
                '--pdf', file_path,
                '--output', output_file,
                '--save-to-db',
                '--db-path', 'data/ocr.db'
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0 and os.path.exists(output_file):
                with open(output_file, 'r', encoding='utf-8') as f:
                    processed_text = f.read()
                return processed_text, None
            else:
                return None, f"PDF processing failed: {result.stderr}"
                
    except subprocess.TimeoutExpired:
        return None, "PDF processing timed out"
    except Exception as e:
        return None, f"PDF processing error: {str(e)}"

def process_audio_file(file_path):
    """Process audio file using the existing asr.py script"""
    try:
        # Create a temporary directory for processing
        with tempfile.TemporaryDirectory() as temp_dir:
            output_file = os.path.join(temp_dir, 'output.txt')
            
            # Run the ASR script
            cmd = [
                'python', 'asr.py',
                '--input', file_path,
                '--output', output_file
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0 and os.path.exists(output_file):
                with open(output_file, 'r', encoding='utf-8') as f:
                    processed_text = f.read()
                return processed_text, None
            else:
                return None, f"Audio processing failed: {result.stderr}"
                
    except subprocess.TimeoutExpired:
        return None, "Audio processing timed out"
    except Exception as e:
        return None, f"Audio processing error: {str(e)}"

def generate_bmc_from_text(text):
    """Generate BMC data from processed text using the existing bmc.py script"""
    try:
        # Create a temporary file with the text
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
            f.write(text)
            temp_text_file = f.name
        
        # Create temporary output files
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
            temp_png_file = f.name
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
            temp_json_file = f.name
        
        try:
            # Run BMC generation
            cmd = [
                'python', 'bmc.py', 'image',
                '--output', temp_png_file,
                '--title', 'Business Model Canvas',
                '--data-file', temp_text_file
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            
            if result.returncode == 0:
                # Try to read the JSON data if it exists
                bmc_data = {}
                json_file = temp_png_file.replace('.png', '_data.json')
                if os.path.exists(json_file):
                    with open(json_file, 'r', encoding='utf-8') as f:
                        bmc_data = json.load(f)
                
                return bmc_data, temp_png_file, None
            else:
                return {}, None, f"BMC generation failed: {result.stderr}"
                
        finally:
            # Clean up temporary files
            for temp_file in [temp_text_file, temp_json_file]:
                if os.path.exists(temp_file):
                    os.unlink(temp_file)
                    
    except subprocess.TimeoutExpired:
        return {}, None, "BMC generation timed out"
    except Exception as e:
        return {}, None, f"BMC generation error: {str(e)}"

# Authentication middleware
def require_auth(f):
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'error': 'Missing or invalid authorization header'}), 401
        
        token = auth_header.split(' ')[1]
        # In a real app, you'd verify the JWT token here
        # For now, we'll use a simple user ID from the token
        try:
            user_id = int(token)
            user = db.get_user_by_id(user_id)
            if not user:
                return jsonify({'error': 'Invalid token'}), 401
            request.current_user = user
        except:
            return jsonify({'error': 'Invalid token'}), 401
        
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

# Routes
@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json()
    
    required_fields = ['username', 'email', 'password', 'role', 'full_name']
    for field in required_fields:
        if not data.get(field):
            return jsonify({'error': f'Missing required field: {field}'}), 400
    
    if data['role'] not in ['admin', 'mentor', 'entrepreneur']:
        return jsonify({'error': 'Invalid role'}), 400
    
    try:
        user_id = db.create_user(
            username=data['username'],
            email=data['email'],
            password=data['password'],
            role=data['role'],
            full_name=data['full_name'],
            phone=data.get('phone')
        )
        
        user = db.get_user_by_id(user_id)
        return jsonify({
            'message': 'User created successfully',
            'user': user
        }), 201
        
    except sqlite3.IntegrityError:
        return jsonify({'error': 'Username or email already exists'}), 409
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    
    if not data.get('username') or not data.get('password'):
        return jsonify({'error': 'Username and password required'}), 400
    
    user = db.authenticate_user(data['username'], data['password'])
    
    if not user:
        return jsonify({'error': 'Invalid credentials'}), 401
    
    # All users are now auto-approved, no approval check needed
    
    # In a real app, you'd generate a JWT token here
    # For now, we'll return the user ID as a simple token
    return jsonify({
        'message': 'Login successful',
        'token': str(user['id']),
        'user': {
            'id': user['id'],
            'username': user['username'],
            'email': user['email'],
            'role': user['role'],
            'full_name': user['full_name'],
            'is_approved': user['is_approved']
        }
    })

@app.route('/api/me', methods=['GET'])
@require_auth
def get_current_user():
    return jsonify({'user': request.current_user})

# Admin routes
@app.route('/api/admin/pending-mentors', methods=['GET'])
@require_auth
def get_pending_mentors():
    if request.current_user['role'] != 'admin':
        return jsonify({'error': 'Admin access required'}), 403
    
    mentors = db.get_pending_mentors()
    return jsonify({'mentors': mentors})

@app.route('/api/admin/approve-mentor/<int:mentor_id>', methods=['POST'])
@require_auth
def approve_mentor(mentor_id):
    if request.current_user['role'] != 'admin':
        return jsonify({'error': 'Admin access required'}), 403
    
    success = db.approve_mentor(mentor_id)
    if success:
        return jsonify({'message': 'Mentor approved successfully'})
    else:
        return jsonify({'error': 'Failed to approve mentor'}), 400

@app.route('/api/admin/assign-mentor', methods=['POST'])
@require_auth
def assign_mentor():
    if request.current_user['role'] != 'admin':
        return jsonify({'error': 'Admin access required'}), 403
    
    data = request.get_json()
    mentor_id = data.get('mentor_id')
    entrepreneur_id = data.get('entrepreneur_id')
    
    if not mentor_id or not entrepreneur_id:
        return jsonify({'error': 'Mentor ID and Entrepreneur ID required'}), 400
    
    success = db.assign_mentor_to_entrepreneur(mentor_id, entrepreneur_id, request.current_user['id'])
    
    if success:
        return jsonify({'message': 'Mentor assigned successfully'})
    else:
        return jsonify({'error': 'Failed to assign mentor'}), 400

@app.route('/api/admin/users', methods=['GET'])
@require_auth
def get_all_users():
    if request.current_user['role'] != 'admin':
        return jsonify({'error': 'Admin access required'}), 403
    
    users = db.get_all_users()
    return jsonify({'users': users})

@app.route('/api/admin/submissions', methods=['GET'])
@require_auth
def get_all_submissions():
    if request.current_user['role'] != 'admin':
        return jsonify({'error': 'Admin access required'}), 403
    
    submissions = db.get_all_submissions()
    return jsonify({'submissions': submissions})

# Mentor routes
@app.route('/api/mentor/entrepreneurs', methods=['GET'])
@require_auth
def get_mentor_entrepreneurs():
    if request.current_user['role'] != 'mentor':
        return jsonify({'error': 'Mentor access required'}), 403
    
    entrepreneurs = db.get_entrepreneurs_for_mentor(request.current_user['id'])
    return jsonify({'entrepreneurs': entrepreneurs})

@app.route('/api/mentor/submissions', methods=['GET'])
@require_auth
def get_mentor_submissions():
    if request.current_user['role'] != 'mentor':
        return jsonify({'error': 'Mentor access required'}), 403
    
    submissions = db.get_submissions_for_mentor(request.current_user['id'])
    return jsonify({'submissions': submissions})

@app.route('/api/mentor/feedback', methods=['POST'])
@require_auth
def create_feedback():
    if request.current_user['role'] != 'mentor':
        return jsonify({'error': 'Mentor access required'}), 403
    
    data = request.get_json()
    submission_id = data.get('submission_id')
    feedback_text = data.get('feedback_text')
    rating = data.get('rating')
    suggestions = data.get('suggestions')
    
    if not submission_id or not feedback_text:
        return jsonify({'error': 'Submission ID and feedback text required'}), 400
    
    feedback_id = db.create_feedback(submission_id, request.current_user['id'], feedback_text, rating, suggestions)
    
    return jsonify({
        'message': 'Feedback created successfully',
        'feedback_id': feedback_id
    })

# Entrepreneur routes
@app.route('/api/entrepreneur/mentor', methods=['GET'])
@require_auth
def get_entrepreneur_mentor():
    if request.current_user['role'] != 'entrepreneur':
        return jsonify({'error': 'Entrepreneur access required'}), 403
    
    mentor = db.get_mentor_for_entrepreneur(request.current_user['id'])
    return jsonify({'mentor': mentor})

@app.route('/api/entrepreneur/submissions', methods=['GET'])
@require_auth
def get_entrepreneur_submissions():
    if request.current_user['role'] != 'entrepreneur':
        return jsonify({'error': 'Entrepreneur access required'}), 403
    
    submissions = db.get_submissions_for_entrepreneur(request.current_user['id'])
    return jsonify({'submissions': submissions})

@app.route('/api/entrepreneur/submit', methods=['POST'])
@require_auth
def submit_file():
    if request.current_user['role'] != 'entrepreneur':
        return jsonify({'error': 'Entrepreneur access required'}), 403
    
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    title = request.form.get('title', '')
    description = request.form.get('description', '')
    
    if not title:
        return jsonify({'error': 'Title is required'}), 400
    
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if not allowed_file(file.filename):
        return jsonify({'error': 'Invalid file type'}), 400
    
    # Save file
    filename = secure_filename(file.filename)
    file_extension = filename.rsplit('.', 1)[1].lower()
    unique_filename = f"{uuid.uuid4()}_{filename}"
    
    if file_extension == 'pdf':
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], 'pdfs', unique_filename)
        file_type = 'pdf'
    else:
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], 'audio', unique_filename)
        file_type = 'audio'
    
    file.save(file_path)
    
    # Create submission record
    submission_id = db.create_submission(
        entrepreneur_id=request.current_user['id'],
        title=title,
        description=description,
        file_path=file_path,
        file_type=file_type,
        original_filename=filename
    )
    
    # Process file in background (in a real app, use Celery or similar)
    try:
        db.add_processing_log(submission_id, 'start', 'processing', 'Starting file processing')
        
        if file_type == 'pdf':
            processed_text, error = process_pdf_file(file_path)
        else:
            processed_text, error = process_audio_file(file_path)
        
        if error:
            db.update_submission_processing(submission_id, status='failed')
            db.add_processing_log(submission_id, 'process', 'failed', error)
            return jsonify({'error': f'Processing failed: {error}'}), 500
        
        # Generate BMC data
        bmc_data, bmc_image_path, bmc_error = generate_bmc_from_text(processed_text)
        
        if bmc_error:
            db.add_processing_log(submission_id, 'bmc', 'failed', bmc_error)
        
        # Update submission
        db.update_submission_processing(
            submission_id, 
            processed_text=processed_text,
            bmc_data=json.dumps(bmc_data) if bmc_data else None,
            status='completed'
        )
        
        db.add_processing_log(submission_id, 'complete', 'success', 'Processing completed successfully')
        
        return jsonify({
            'message': 'File submitted and processed successfully',
            'submission_id': submission_id,
            'processed_text': processed_text,
            'bmc_data': bmc_data
        })
        
    except Exception as e:
        db.update_submission_processing(submission_id, status='failed')
        db.add_processing_log(submission_id, 'error', 'failed', str(e))
        return jsonify({'error': f'Processing error: {str(e)}'}), 500

@app.route('/api/submissions/<int:submission_id>/feedback', methods=['GET'])
@require_auth
def get_submission_feedback(submission_id):
    feedback = db.get_feedback_for_submission(submission_id)
    return jsonify({'feedback': feedback})

@app.route('/api/submissions/<int:submission_id>', methods=['GET'])
@require_auth
def get_submission(submission_id):
    # Get submission details (implement this in database.py if needed)
    return jsonify({'message': 'Submission details endpoint'})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
