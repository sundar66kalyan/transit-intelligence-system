# utils/database.py (Updated with entry/exit tracking)
import sqlite3
import json
from datetime import datetime
import os

DB_PATH = "D:/VehicleSurveillanceSystem/data/surveillance.db"

def init_database():
    """Initialize SQLite database with required tables"""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Passengers table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS passengers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            passenger_id TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            passenger_type TEXT,
            face_image_path TEXT,
            is_blacklisted BOOLEAN DEFAULT 0,
            registered_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_active BOOLEAN DEFAULT 1
        )
    ''')
    
    # Entry/Exit Logs table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS entry_exit_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            passenger_id TEXT,
            passenger_name TEXT,
            event_type TEXT CHECK(event_type IN ('ENTRY', 'EXIT')),
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            location_lat REAL,
            location_lon REAL,
            location_address TEXT,
            bus_id TEXT,
            confidence REAL,
            is_registered BOOLEAN,
            alert_generated BOOLEAN DEFAULT 0
        )
    ''')
    
    # Alerts table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            alert_id TEXT UNIQUE NOT NULL,
            alert_type TEXT,
            severity TEXT,
            message TEXT,
            location TEXT,
            passenger_info TEXT,
            timestamp TIMESTAMP,
            status TEXT DEFAULT 'ACTIVE',
            resolved_at TIMESTAMP
        )
    ''')
    
    # Attendance table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            passenger_id TEXT NOT NULL,
            bus_id TEXT NOT NULL,
            date TEXT NOT NULL,
            entry_time TEXT,
            exit_time TEXT,
            status TEXT DEFAULT 'present',
            journey_id TEXT
        )
    ''')
    
    conn.commit()
    conn.close()
    print("✅ Database initialized with entry/exit tracking")

def log_entry_exit(passenger_id, passenger_name, event_type, location, bus_id, confidence, is_registered):
    """Log passenger entry or exit"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO entry_exit_logs 
        (passenger_id, passenger_name, event_type, location_lat, location_lon, 
         location_address, bus_id, confidence, is_registered, alert_generated)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        passenger_id, passenger_name, event_type,
        location.get("lat"), location.get("lon"),
        location.get("address"), bus_id, confidence, is_registered, 0
    ))
    
    conn.commit()
    conn.close()
    return True

def get_recent_entries(limit=50):
    """Get recent entry/exit logs"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT passenger_name, event_type, timestamp, location_address, bus_id, is_registered
        FROM entry_exit_logs
        ORDER BY timestamp DESC
        LIMIT ?
    ''', (limit,))
    
    results = cursor.fetchall()
    conn.close()
    
    return [
        {
            "passenger_name": r[0],
            "event_type": r[1],
            "timestamp": r[2],
            "location": r[3],
            "bus_id": r[4],
            "is_registered": r[5]
        }
        for r in results
    ]

def save_alert(alert):
    """Save alert to database"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT OR REPLACE INTO alerts 
        (alert_id, alert_type, severity, message, location, passenger_info, timestamp, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        alert["alert_id"], alert["type"], alert["severity"],
        alert["message"], json.dumps(alert["location"]),
        json.dumps(alert["passenger"]), alert["timestamp"], alert["status"]
    ))
    
    conn.commit()
    conn.close()

def register_passenger(passenger_id, name, passenger_type, face_image_path=None, is_blacklisted=False):
    """Register a new passenger"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            INSERT OR REPLACE INTO passengers 
            (passenger_id, name, passenger_type, face_image_path, is_blacklisted)
            VALUES (?, ?, ?, ?, ?)
        ''', (passenger_id, name, passenger_type, face_image_path, is_blacklisted))
        conn.commit()
        return True
    except Exception as e:
        print(f"Error registering passenger: {e}")
        return False
    finally:
        conn.close()

def is_passenger_blacklisted(passenger_id):
    """Check if passenger is blacklisted"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('SELECT is_blacklisted FROM passengers WHERE passenger_id = ?', (passenger_id,))
    result = cursor.fetchone()
    conn.close()
    
    return result[0] == 1 if result else False

def get_all_passengers():
    """Get all registered passengers"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT passenger_id, name, passenger_type, face_image_path, is_blacklisted FROM passengers WHERE is_active = 1')
    results = cursor.fetchall()
    conn.close()
    
    return [
        {
            "passenger_id": r[0],
            "name": r[1],
            "passenger_type": r[2],
            "face_image": r[3],
            "is_blacklisted": r[4]
        }
        for r in results
    ]

# Initialize database
init_database()
