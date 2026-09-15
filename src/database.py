"""
src/database.py - SQLite database with performance learning
"""

import sqlite3
import json
import hashlib
from datetime import datetime, timedelta
from src.config import DATABASE_CONFIG, PATHS
import os

def get_connection():
    """Get database connection"""
    os.makedirs(PATHS['data'], exist_ok=True)
    conn = sqlite3.connect(
        DATABASE_CONFIG['path'],
        timeout=DATABASE_CONFIG['timeout'],
        check_same_thread=DATABASE_CONFIG['check_same_thread']
    )
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize database schema"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Sources table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sources (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            url TEXT UNIQUE,
            domain TEXT,
            tier INTEGER DEFAULT 4,
            credibility_score REAL DEFAULT 50,
            last_checked TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Stories table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS stories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            canonical_topic TEXT,
            url TEXT,
            source TEXT,
            source_tier INTEGER DEFAULT 4,
            breakout_score REAL DEFAULT 0,
            search_volume REAL DEFAULT 0,
            trend_score REAL DEFAULT 0,
            global_score REAL DEFAULT 0,
            final_score REAL DEFAULT 0,
            keywords TEXT,
            entities TEXT,
            script_hash TEXT,
            video_hash TEXT,
            status TEXT DEFAULT 'pending',
            rejection_reason TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Claims table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS claims (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            story_id INTEGER,
            claim_text TEXT,
            source_url TEXT,
            source_type TEXT,
            verification_status TEXT DEFAULT 'unverified',
            confidence REAL DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (story_id) REFERENCES stories(id)
        )
    ''')
    
    # Scripts table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS scripts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            story_id INTEGER,
            short_script TEXT,
            long_script TEXT,
            title TEXT,
            description TEXT,
            hashtags TEXT,
            tags TEXT,
            fact_map TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (story_id) REFERENCES stories(id)
        )
    ''')
    
    # Videos table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS videos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            story_id INTEGER,
            video_path TEXT,
            thumbnail_path TEXT,
            duration REAL,
            fps REAL,
            resolution TEXT,
            file_size INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (story_id) REFERENCES stories(id)
        )
    ''')
    
    # Uploads table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS uploads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            story_id INTEGER,
            video_id TEXT UNIQUE,
            youtube_url TEXT,
            title TEXT,
            privacy_status TEXT DEFAULT 'public',
            uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (story_id) REFERENCES stories(id)
        )
    ''')
    
    # Performance table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS performance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            video_id TEXT,
            views INTEGER DEFAULT 0,
            likes INTEGER DEFAULT 0,
            comments INTEGER DEFAULT 0,
            shares INTEGER DEFAULT 0,
            avg_view_duration REAL DEFAULT 0,
            avg_percentage_viewed REAL DEFAULT 0,
            subscribers_gained INTEGER DEFAULT 0,
            retention_score REAL DEFAULT 0,
            engagement_score REAL DEFAULT 0,
            collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (video_id) REFERENCES uploads(video_id)
        )
    ''')
    
    # Trend signals table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS trend_signals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            topic TEXT,
            signal_type TEXT,
            signal_value REAL,
            geo TEXT,
            collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Errors table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS errors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            component TEXT,
            error_message TEXT,
            stack_trace TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()
    print("[DB] Database initialized with all tables")

def save_story(story_data):
    """Save story to database, return story_id"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Generate hashes
    script_text = story_data.get('short_script', '') or story_data.get('full_script', '')
    script_hash = hashlib.md5(script_text.encode()).hexdigest() if script_text else ""
    
    title = story_data.get('title', '') or story_data.get('seo_youtube_title', '')
    
    cursor.execute('''
        INSERT INTO stories (title, canonical_topic, url, source, source_tier, 
                           breakout_score, search_volume, trend_score, global_score,
                           final_score, keywords, entities, script_hash, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        title,
        story_data.get('canonical_topic', title[:50]),
        story_data.get('url', ''),
        story_data.get('source', ''),
        story_data.get('source_tier', 4),
        story_data.get('breakout_score', 0),
        story_data.get('search_volume', 0),
        story_data.get('trend_score', 0),
        story_data.get('global_score', 0),
        story_data.get('final_score', 0),
        json.dumps(story_data.get('keywords', [])),
        json.dumps(story_data.get('entities', [])),
        script_hash,
        'pending'
    ))
    
    story_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    print(f"[DB] Saved story {story_id}: {title[:50]}")
    return story_id

def mark_uploaded(story_id, video_id):
    """Mark story as uploaded"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        UPDATE stories SET status = 'uploaded', updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
    ''', (story_id,))
    
    cursor.execute('''
        INSERT INTO uploads (story_id, video_id, youtube_url)
        VALUES (?, ?, ?)
    ''', (story_id, video_id, f"https://youtu.be/{video_id}"))
    
    conn.commit()
    conn.close()
    
    print(f"[DB] Marked story {story_id} as uploaded: {video_id}")

def get_performance_stats():
    """Get performance statistics for learning"""
    conn = get_connection()
    cursor = conn.cursor()
    
    stats = {}
    
    # Total uploads
    cursor.execute("SELECT COUNT(*) FROM uploads")
    stats['total_uploads'] = cursor.fetchone()[0]
    
    # Total stories processed
    cursor.execute("SELECT COUNT(*) FROM stories")
    stats['total_stories'] = cursor.fetchone()[0]
    
    # Uploaded stories
    cursor.execute("SELECT COUNT(*) FROM stories WHERE status = 'uploaded'")
    stats['uploaded'] = cursor.fetchone()[0]
    
    # Rejected stories
    cursor.execute("SELECT COUNT(*) FROM stories WHERE status = 'rejected'")
    stats['rejected'] = cursor.fetchone()[0]
    
    # Average performance (if available)
    cursor.execute('''
        SELECT AVG(views), AVG(likes), AVG(avg_percentage_viewed)
        FROM performance
    ''')
    row = cursor.fetchone()
    if row and row[0]:
        stats['avg_views'] = row[0]
        stats['avg_likes'] = row[1]
        stats['avg_retention'] = row[2]
    
    conn.close()
    return stats

def get_recent_stories(limit=10):
    """Get recent stories"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT * FROM stories ORDER BY created_at DESC LIMIT ?
    ''', (limit,))
    
    rows = cursor.fetchall()
    conn.close()
    
    return [dict(row) for row in rows]

def log_error(component, error_message, stack_trace=""):
    """Log error to database"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO errors (component, error_message, stack_trace)
        VALUES (?, ?, ?)
    ''', (component, error_message, stack_trace))
    
    conn.commit()
    conn.close()

# ============================================================
# PERFORMANCE LEARNING
# ============================================================

def save_performance(video_id, performance_data):
    """Save performance data for a video"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO performance (video_id, views, likes, comments, shares,
                               avg_view_duration, avg_percentage_viewed,
                               subscribers_gained, retention_score, engagement_score)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        video_id,
        performance_data.get('views', 0),
        performance_data.get('likes', 0),
        performance_data.get('comments', 0),
        performance_data.get('shares', 0),
        performance_data.get('avg_view_duration', 0),
        performance_data.get('avg_percentage_viewed', 0),
        performance_data.get('subscribers_gained', 0),
        performance_data.get('retention_score', 0),
        performance_data.get('engagement_score', 0)
    ))
    
    conn.commit()
    conn.close()

def get_topic_performance():
    """Get performance by topic for learning"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT s.canonical_topic, AVG(p.views) as avg_views, 
               AVG(p.avg_percentage_viewed) as avg_retention
        FROM stories s
        JOIN uploads u ON s.id = u.story_id
        JOIN performance p ON u.video_id = p.video_id
        GROUP BY s.canonical_topic
        ORDER BY avg_views DESC
    ''')
    
    rows = cursor.fetchall()
    conn.close()
    
    return [dict(row) for row in rows]
