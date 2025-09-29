"""
Database setup and models for the CSI Hackathon application
"""

import sqlite3
import hashlib
import os
from datetime import datetime
from typing import Optional, List, Dict, Any
from pathlib import Path

class Database:
    def __init__(self, db_path: str = "data/app.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize the database with all required tables"""
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Users table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    role TEXT NOT NULL CHECK(role IN ('admin', 'mentor', 'entrepreneur')),
                    full_name TEXT NOT NULL,
                    phone TEXT,
                    is_approved INTEGER DEFAULT 1,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)
            
            # Mentor-Entrepreneur assignments
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS mentor_assignments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    mentor_id INTEGER NOT NULL,
                    entrepreneur_id INTEGER NOT NULL,
                    assigned_at TEXT NOT NULL,
                    assigned_by INTEGER NOT NULL,
                    status TEXT DEFAULT 'active' CHECK(status IN ('active', 'inactive')),
                    FOREIGN KEY (mentor_id) REFERENCES users (id),
                    FOREIGN KEY (entrepreneur_id) REFERENCES users (id),
                    FOREIGN KEY (assigned_by) REFERENCES users (id),
                    UNIQUE(mentor_id, entrepreneur_id)
                )
            """)
            
            # Submissions table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS submissions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    entrepreneur_id INTEGER NOT NULL,
                    title TEXT NOT NULL,
                    description TEXT,
                    file_path TEXT,
                    file_type TEXT CHECK(file_type IN ('pdf', 'audio')),
                    original_filename TEXT,
                    processed_text TEXT,
                    bmc_data TEXT,  -- JSON string of BMC data
                    status TEXT DEFAULT 'pending' CHECK(status IN ('pending', 'processing', 'completed', 'failed')),
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    FOREIGN KEY (entrepreneur_id) REFERENCES users (id)
                )
            """)
            
            # Feedback table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS feedback (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    submission_id INTEGER NOT NULL,
                    mentor_id INTEGER NOT NULL,
                    feedback_text TEXT NOT NULL,
                    rating INTEGER CHECK(rating >= 1 AND rating <= 5),
                    suggestions TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    FOREIGN KEY (submission_id) REFERENCES submissions (id),
                    FOREIGN KEY (mentor_id) REFERENCES users (id)
                )
            """)
            
            # Processing logs
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS processing_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    submission_id INTEGER NOT NULL,
                    step TEXT NOT NULL,
                    status TEXT NOT NULL,
                    message TEXT,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (submission_id) REFERENCES submissions (id)
                )
            """)
            
            conn.commit()
    
    def hash_password(self, password: str) -> str:
        """Hash password using SHA-256 with salt"""
        salt = os.urandom(32)
        pwd_hash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
        return salt.hex() + pwd_hash.hex()
    
    def verify_password(self, password: str, stored_hash: str) -> bool:
        """Verify password against stored hash"""
        try:
            salt = bytes.fromhex(stored_hash[:64])
            stored_pwd_hash = stored_hash[64:]
            pwd_hash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
            return pwd_hash.hex() == stored_pwd_hash
        except:
            return False
    
    def create_user(self, username: str, email: str, password: str, role: str, full_name: str, phone: str = None) -> int:
        """Create a new user"""
        password_hash = self.hash_password(password)
        now = datetime.now().isoformat()
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO users (username, email, password_hash, role, full_name, phone, is_approved, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (username, email, password_hash, role, full_name, phone, 1, now, now))
            return cursor.lastrowid
    
    def authenticate_user(self, username: str, password: str) -> Optional[Dict[str, Any]]:
        """Authenticate user and return user data if successful"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, username, email, password_hash, role, full_name, phone, is_approved
                FROM users WHERE username = ?
            """, (username,))
            user = cursor.fetchone()
            
            if user and self.verify_password(password, user['password_hash']):
                return dict(user)
            return None
    
    def get_user_by_id(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get user by ID"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, username, email, role, full_name, phone, is_approved, created_at
                FROM users WHERE id = ?
            """, (user_id,))
            user = cursor.fetchone()
            return dict(user) if user else None
    
    def get_pending_mentors(self) -> List[Dict[str, Any]]:
        """Get all pending mentor approvals (now returns empty list since all users are auto-approved)"""
        return []
    
    def approve_mentor(self, mentor_id: int) -> bool:
        """Approve a mentor (now always returns True since all users are auto-approved)"""
        return True
    
    def assign_mentor_to_entrepreneur(self, mentor_id: int, entrepreneur_id: int, assigned_by: int) -> bool:
        """Assign a mentor to an entrepreneur"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            try:
                cursor.execute("""
                    INSERT INTO mentor_assignments (mentor_id, entrepreneur_id, assigned_at, assigned_by)
                    VALUES (?, ?, ?, ?)
                """, (mentor_id, entrepreneur_id, datetime.now().isoformat(), assigned_by))
                return True
            except sqlite3.IntegrityError:
                return False
    
    def get_entrepreneurs_for_mentor(self, mentor_id: int) -> List[Dict[str, Any]]:
        """Get all entrepreneurs assigned to a mentor"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("""
                SELECT u.id, u.username, u.email, u.full_name, u.phone, ma.assigned_at
                FROM users u
                JOIN mentor_assignments ma ON u.id = ma.entrepreneur_id
                WHERE ma.mentor_id = ? AND ma.status = 'active'
                ORDER BY ma.assigned_at DESC
            """, (mentor_id,))
            return [dict(row) for row in cursor.fetchall()]
    
    def get_mentor_for_entrepreneur(self, entrepreneur_id: int) -> Optional[Dict[str, Any]]:
        """Get the mentor assigned to an entrepreneur"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("""
                SELECT u.id, u.username, u.email, u.full_name, u.phone, ma.assigned_at
                FROM users u
                JOIN mentor_assignments ma ON u.id = ma.mentor_id
                WHERE ma.entrepreneur_id = ? AND ma.status = 'active'
            """, (entrepreneur_id,))
            mentor = cursor.fetchone()
            return dict(mentor) if mentor else None
    
    def create_submission(self, entrepreneur_id: int, title: str, description: str, 
                         file_path: str, file_type: str, original_filename: str) -> int:
        """Create a new submission"""
        now = datetime.now().isoformat()
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO submissions (entrepreneur_id, title, description, file_path, file_type, 
                                       original_filename, status, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, 'pending', ?, ?)
            """, (entrepreneur_id, title, description, file_path, file_type, original_filename, now, now))
            return cursor.lastrowid
    
    def update_submission_processing(self, submission_id: int, processed_text: str = None, 
                                   bmc_data: str = None, status: str = 'completed') -> bool:
        """Update submission with processing results"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE submissions 
                SET processed_text = ?, bmc_data = ?, status = ?, updated_at = ?
                WHERE id = ?
            """, (processed_text, bmc_data, status, datetime.now().isoformat(), submission_id))
            return cursor.rowcount > 0
    
    def get_submissions_for_entrepreneur(self, entrepreneur_id: int) -> List[Dict[str, Any]]:
        """Get all submissions for an entrepreneur"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("""
                SELECT s.*, COUNT(f.id) as feedback_count
                FROM submissions s
                LEFT JOIN feedback f ON s.id = f.submission_id
                WHERE s.entrepreneur_id = ?
                GROUP BY s.id
                ORDER BY s.created_at DESC
            """, (entrepreneur_id,))
            return [dict(row) for row in cursor.fetchall()]
    
    def get_submissions_for_mentor(self, mentor_id: int) -> List[Dict[str, Any]]:
        """Get all submissions from entrepreneurs assigned to a mentor"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("""
                SELECT s.*, u.full_name as entrepreneur_name, u.username as entrepreneur_username,
                       COUNT(f.id) as feedback_count
                FROM submissions s
                JOIN users u ON s.entrepreneur_id = u.id
                JOIN mentor_assignments ma ON u.id = ma.entrepreneur_id
                LEFT JOIN feedback f ON s.id = f.submission_id
                WHERE ma.mentor_id = ? AND ma.status = 'active'
                GROUP BY s.id
                ORDER BY s.created_at DESC
            """, (mentor_id,))
            return [dict(row) for row in cursor.fetchall()]
    
    def create_feedback(self, submission_id: int, mentor_id: int, feedback_text: str, 
                       rating: int = None, suggestions: str = None) -> int:
        """Create feedback for a submission"""
        now = datetime.now().isoformat()
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO feedback (submission_id, mentor_id, feedback_text, rating, suggestions, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (submission_id, mentor_id, feedback_text, rating, suggestions, now, now))
            return cursor.lastrowid
    
    def get_feedback_for_submission(self, submission_id: int) -> List[Dict[str, Any]]:
        """Get all feedback for a submission"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("""
                SELECT f.*, u.full_name as mentor_name, u.username as mentor_username
                FROM feedback f
                JOIN users u ON f.mentor_id = u.id
                WHERE f.submission_id = ?
                ORDER BY f.created_at DESC
            """, (submission_id,))
            return [dict(row) for row in cursor.fetchall()]
    
    def get_all_users(self) -> List[Dict[str, Any]]:
        """Get all users (admin only)"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, username, email, role, full_name, phone, is_approved, created_at
                FROM users
                ORDER BY created_at DESC
            """)
            return [dict(row) for row in cursor.fetchall()]
    
    def get_all_submissions(self) -> List[Dict[str, Any]]:
        """Get all submissions (admin only)"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("""
                SELECT s.*, u.full_name as entrepreneur_name, u.username as entrepreneur_username,
                       COUNT(f.id) as feedback_count
                FROM submissions s
                JOIN users u ON s.entrepreneur_id = u.id
                LEFT JOIN feedback f ON s.id = f.submission_id
                GROUP BY s.id
                ORDER BY s.created_at DESC
            """)
            return [dict(row) for row in cursor.fetchall()]
    
    def add_processing_log(self, submission_id: int, step: str, status: str, message: str = None):
        """Add a processing log entry"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO processing_logs (submission_id, step, status, message, created_at)
                VALUES (?, ?, ?, ?, ?)
            """, (submission_id, step, status, message, datetime.now().isoformat()))

# Initialize database
db = Database()
