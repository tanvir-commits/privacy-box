#!/usr/bin/env python3
"""
Privacy Dashboard - Web interface for per-device tracking visualization
"""

from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
import sqlite3
import json
from datetime import datetime, timedelta
from collections import defaultdict

# Try to use installed paths, fallback to local for development
import os
template_dir = '/usr/share/privacy-dashboard/templates' if os.path.exists('/usr/share/privacy-dashboard/templates') else os.path.join(os.path.dirname(__file__), 'templates')
static_dir = '/usr/share/privacy-dashboard/static' if os.path.exists('/usr/share/privacy-dashboard/static') else os.path.join(os.path.dirname(__file__), 'static')

app = Flask(__name__, 
            template_folder=template_dir,
            static_folder=static_dir)
CORS(app)

DB_PATH = "/var/lib/device-tracker/device_tracker.db"

def get_db():
    """Get database connection"""
    return sqlite3.connect(DB_PATH)

@app.route('/')
def index():
    """Main dashboard page"""
    return render_template('index.html')

@app.route('/api/devices')
def get_devices():
    """Get list of all devices"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT DISTINCT ip, mac, name, MAX(last_seen) as last_seen
        FROM devices
        GROUP BY ip
        ORDER BY last_seen DESC
    """)
    devices = []
    for row in cursor.fetchall():
        devices.append({
            'ip': row[0],
            'mac': row[1],
            'name': row[2] or 'Unknown',
            'last_seen': row[3]
        })
    conn.close()
    return jsonify(devices)

@app.route('/api/device/<ip>/stats')
def get_device_stats(ip):
    """Get statistics for a specific device"""
    conn = get_db()
    cursor = conn.cursor()
    
    # Get device info
    cursor.execute("SELECT mac, name FROM devices WHERE ip = ?", (ip,))
    device_info = cursor.fetchone()
    if not device_info:
        return jsonify({'error': 'Device not found'}), 404
    
    # Get query stats (last 24 hours)
    since = int((datetime.now() - timedelta(hours=24)).timestamp())
    cursor.execute("""
        SELECT 
            COUNT(*) as total_queries,
            SUM(CASE WHEN is_tracker = 1 THEN 1 ELSE 0 END) as tracker_queries,
            SUM(CASE WHEN blocked = 1 THEN 1 ELSE 0 END) as blocked_queries,
            COUNT(DISTINCT domain) as unique_domains
        FROM dns_queries
        WHERE device_ip = ? AND timestamp > ?
    """, (ip, since))
    
    stats = cursor.fetchone()
    
    # Get top trackers
    cursor.execute("""
        SELECT domain, COUNT(*) as count
        FROM dns_queries
        WHERE device_ip = ? AND is_tracker = 1 AND timestamp > ?
        GROUP BY domain
        ORDER BY count DESC
        LIMIT 10
    """, (ip, since))
    
    top_trackers = [{'domain': row[0], 'count': row[1]} for row in cursor.fetchall()]
    
    conn.close()
    
    return jsonify({
        'device': {
            'ip': ip,
            'mac': device_info[0],
            'name': device_info[1] or 'Unknown'
        },
        'stats': {
            'total_queries': stats[0] or 0,
            'tracker_queries': stats[1] or 0,
            'blocked_queries': stats[2] or 0,
            'unique_domains': stats[3] or 0
        },
        'top_trackers': top_trackers
    })

@app.route('/api/network/stats')
def get_network_stats():
    """Get overall network statistics"""
    conn = get_db()
    cursor = conn.cursor()
    
    since = int((datetime.now() - timedelta(hours=24)).timestamp())
    
    cursor.execute("""
        SELECT 
            COUNT(*) as total_queries,
            SUM(CASE WHEN is_tracker = 1 THEN 1 ELSE 0 END) as tracker_queries,
            SUM(CASE WHEN blocked = 1 THEN 1 ELSE 0 END) as blocked_queries,
            COUNT(DISTINCT device_ip) as device_count
        FROM dns_queries
        WHERE timestamp > ?
    """, (since,))
    
    stats = cursor.fetchone()
    
    # Get per-device breakdown
    cursor.execute("""
        SELECT 
            device_ip,
            device_name,
            COUNT(*) as queries,
            SUM(CASE WHEN is_tracker = 1 THEN 1 ELSE 0 END) as trackers
        FROM dns_queries
        WHERE timestamp > ?
        GROUP BY device_ip
        ORDER BY trackers DESC
    """, (since,))
    
    devices = []
    for row in cursor.fetchall():
        devices.append({
            'ip': row[0],
            'name': row[1] or 'Unknown',
            'queries': row[2],
            'trackers': row[3]
        })
    
    conn.close()
    
    return jsonify({
        'network': {
            'total_queries': stats[0] or 0,
            'tracker_queries': stats[1] or 0,
            'blocked_queries': stats[2] or 0,
            'device_count': stats[3] or 0
        },
        'devices': devices
    })

@app.route('/api/realtime')
def get_realtime():
    """Get real-time updates (last 5 minutes)"""
    conn = get_db()
    cursor = conn.cursor()
    
    since = int((datetime.now() - timedelta(minutes=5)).timestamp())
    
    cursor.execute("""
        SELECT device_ip, device_name, domain, is_tracker, blocked, timestamp
        FROM dns_queries
        WHERE timestamp > ?
        ORDER BY timestamp DESC
        LIMIT 100
    """, (since,))
    
    queries = []
    for row in cursor.fetchall():
        queries.append({
            'device_ip': row[0],
            'device_name': row[1] or 'Unknown',
            'domain': row[2],
            'is_tracker': bool(row[3]),
            'blocked': bool(row[4]),
            'timestamp': row[5]
        })
    
    conn.close()
    return jsonify(queries)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=False)

