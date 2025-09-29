#!/usr/bin/env python3
"""
Simple script to view database contents
"""

import sqlite3
from database import db

def view_database():
    """View all tables and their contents"""
    
    with sqlite3.connect(db.db_path) as conn:
        cursor = conn.cursor()
        
        # Get all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        print("🗄️  Database Tables:")
        print("=" * 50)
        
        for table in tables:
            table_name = table[0]
            print(f"\n📋 Table: {table_name}")
            print("-" * 30)
            
            # Get table schema
            cursor.execute(f"PRAGMA table_info({table_name});")
            columns = cursor.fetchall()
            
            print("Columns:")
            for col in columns:
                print(f"  - {col[1]} ({col[2]})")
            
            # Get row count
            cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
            count = cursor.fetchone()[0]
            print(f"Rows: {count}")
            
            # Show sample data (first 5 rows)
            if count > 0:
                cursor.execute(f"SELECT * FROM {table_name} LIMIT 5;")
                rows = cursor.fetchall()
                
                print("Sample data:")
                for i, row in enumerate(rows, 1):
                    print(f"  {i}: {row}")
                
                if count > 5:
                    print(f"  ... and {count - 5} more rows")

def view_users():
    """View all users"""
    print("\n👥 Users:")
    print("=" * 50)
    
    users = db.get_all_users()
    for user in users:
        print(f"ID: {user['id']}")
        print(f"Name: {user['full_name']}")
        print(f"Username: {user['username']}")
        print(f"Email: {user['email']}")
        print(f"Role: {user['role']}")
        print(f"Approved: {'Yes' if user['is_approved'] else 'No'}")
        print(f"Created: {user['created_at']}")
        print("-" * 30)

def view_submissions():
    """View all submissions"""
    print("\n📄 Submissions:")
    print("=" * 50)
    
    with sqlite3.connect(db.db_path) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT s.*, u.full_name as entrepreneur_name
            FROM submissions s
            JOIN users u ON s.entrepreneur_id = u.id
            ORDER BY s.created_at DESC
        """)
        
        submissions = cursor.fetchall()
        
        for sub in submissions:
            print(f"ID: {sub['id']}")
            print(f"Title: {sub['title']}")
            print(f"Entrepreneur: {sub['entrepreneur_name']}")
            print(f"File Type: {sub['file_type']}")
            print(f"Status: {sub['status']}")
            print(f"Created: {sub['created_at']}")
            print("-" * 30)

def view_feedback():
    """View all feedback"""
    print("\n💬 Feedback:")
    print("=" * 50)
    
    with sqlite3.connect(db.db_path) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT f.*, u1.full_name as mentor_name, u2.full_name as entrepreneur_name
            FROM feedback f
            JOIN users u1 ON f.mentor_id = u1.id
            JOIN submissions s ON f.submission_id = s.id
            JOIN users u2 ON s.entrepreneur_id = u2.id
            ORDER BY f.created_at DESC
        """)
        
        feedback = cursor.fetchall()
        
        for fb in feedback:
            print(f"ID: {fb['id']}")
            print(f"Mentor: {fb['mentor_name']}")
            print(f"Entrepreneur: {fb['entrepreneur_name']}")
            print(f"Rating: {fb['rating'] or 'No rating'}")
            print(f"Feedback: {fb['feedback_text'][:100]}...")
            print(f"Created: {fb['created_at']}")
            print("-" * 30)

if __name__ == "__main__":
    print("🔍 CSI Hackathon Database Viewer")
    print("=" * 50)
    
    try:
        # View all tables
        view_database()
        
        # View specific data
        view_users()
        view_submissions()
        view_feedback()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print("Make sure the database exists and the app has been run at least once.")
