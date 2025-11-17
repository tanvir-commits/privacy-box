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

def get_device_name(cursor, ip):
    """Get most up-to-date device name"""
    # First try devices table (most authoritative)
    cursor.execute("SELECT name FROM devices WHERE ip = ?", (ip,))
    row = cursor.fetchone()
    if row and row[0] and row[0] != 'Unknown':
        return row[0]
    
    # Fallback to most recent name from dns_queries
    cursor.execute("""
        SELECT device_name FROM dns_queries 
        WHERE device_ip = ? AND device_name IS NOT NULL AND device_name != 'Unknown' 
        ORDER BY timestamp DESC LIMIT 1
    """, (ip,))
    row = cursor.fetchone()
    if row and row[0]:
        return row[0]
    
    return 'Unknown'

def get_device_type(device_name):
    """Determine device type from device name"""
    if not device_name or device_name == 'Unknown':
        return 'unknown'
    
    name_lower = device_name.lower()
    
    # Apple devices
    if 'iphone' in name_lower:
        return 'iphone'
    if 'ipad' in name_lower:
        return 'ipad'
    if 'ipod' in name_lower:
        return 'ipod'
    if 'apple' in name_lower:
        return 'apple'
    
    # Android devices
    if 'android phone' in name_lower:
        return 'android-phone'
    if 'android tablet' in name_lower:
        return 'android-tablet'
    if 'android' in name_lower:
        return 'android'
    
    # Windows devices
    if 'windows pc' in name_lower or 'windows laptop' in name_lower:
        return 'windows-pc'
    if 'windows' in name_lower:
        return 'windows'
    
    return 'generic'

def get_device_icon(device_type):
    """Get icon emoji for device type"""
    icon_map = {
        'iphone': '📱',
        'ipad': '📱',
        'ipod': '🎵',
        'apple': '🍎',
        'android-phone': '📱',
        'android-tablet': '📱',
        'android': '🤖',
        'windows-pc': '💻',
        'windows': '🪟',
        'generic': '🖥️',
        'unknown': '❓'
    }
    return icon_map.get(device_type, '🖥️')

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
        SELECT DISTINCT ip, mac, MAX(last_seen) as last_seen
        FROM devices
        GROUP BY ip
        ORDER BY last_seen DESC
    """)
    devices = []
    for row in cursor.fetchall():
        device_ip = row[0]
        # Get most up-to-date device name
        device_name = get_device_name(cursor, device_ip)
        device_type = get_device_type(device_name)
        device_icon = get_device_icon(device_type)
        devices.append({
            'ip': device_ip,
            'mac': row[1],
            'name': device_name,
            'type': device_type,
            'icon': device_icon,
            'last_seen': row[2]
        })
    conn.close()
    return jsonify(devices)

@app.route('/api/device/<ip>/stats')
def get_device_stats(ip):
    """Get statistics for a specific device"""
    conn = get_db()
    cursor = conn.cursor()
    
    # Get device info
    cursor.execute("SELECT mac FROM devices WHERE ip = ?", (ip,))
    device_info = cursor.fetchone()
    if not device_info:
        return jsonify({'error': 'Device not found'}), 404
    
    # Get most up-to-date device name
    device_name = get_device_name(cursor, ip)
    device_type = get_device_type(device_name)
    device_icon = get_device_icon(device_type)
    
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
        LIMIT 20
    """, (ip, since))
    
    top_trackers = [{'domain': row[0], 'count': row[1]} for row in cursor.fetchall()]
    
    # Get top domains (all queries, not just trackers)
    cursor.execute("""
        SELECT domain, COUNT(*) as count
        FROM dns_queries
        WHERE device_ip = ? AND timestamp > ?
        GROUP BY domain
        ORDER BY count DESC
        LIMIT 20
    """, (ip, since))
    
    top_domains = [{'domain': row[0], 'count': row[1]} for row in cursor.fetchall()]
    
    # Get recent activity (last hour)
    hour_ago = int((datetime.now() - timedelta(hours=1)).timestamp())
    cursor.execute("""
        SELECT domain, is_tracker, blocked, timestamp
        FROM dns_queries
        WHERE device_ip = ? AND timestamp > ?
        ORDER BY timestamp DESC
        LIMIT 50
    """, (ip, hour_ago))
    
    recent_activity = []
    for row in cursor.fetchall():
        recent_activity.append({
            'domain': row[0],
            'is_tracker': bool(row[1]),
            'blocked': bool(row[2]),
            'timestamp': row[3]
        })
    
    conn.close()
    
    return jsonify({
        'device': {
            'ip': ip,
            'mac': device_info[0],
            'name': device_name,
            'type': device_type,
            'icon': device_icon
        },
        'stats': {
            'total_queries': stats[0] or 0,
            'tracker_queries': stats[1] or 0,
            'blocked_queries': stats[2] or 0,
            'unique_domains': stats[3] or 0
        },
        'top_trackers': top_trackers,
        'top_domains': top_domains,
        'recent_activity': recent_activity
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
            COUNT(*) as queries,
            SUM(CASE WHEN is_tracker = 1 THEN 1 ELSE 0 END) as trackers
        FROM dns_queries
        WHERE timestamp > ?
        GROUP BY device_ip
        ORDER BY trackers DESC
    """, (since,))
    
    devices = []
    for row in cursor.fetchall():
        device_ip = row[0]
        # Get most up-to-date device name
        device_name = get_device_name(cursor, device_ip)
        device_type = get_device_type(device_name)
        device_icon = get_device_icon(device_type)
        devices.append({
            'ip': device_ip,
            'name': device_name,
            'type': device_type,
            'icon': device_icon,
            'queries': row[1],
            'trackers': row[2]
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
        device_ip = row[0]
        # Get most up-to-date device name
        device_name = get_device_name(cursor, device_ip)
        device_type = get_device_type(device_name)
        device_icon = get_device_icon(device_type)
        queries.append({
            'device_ip': device_ip,
            'device_name': device_name,
            'device_type': device_type,
            'device_icon': device_icon,
            'domain': row[2],
            'is_tracker': bool(row[3]),
            'blocked': bool(row[4]),
            'timestamp': row[5]
        })
    
    conn.close()
    return jsonify(queries)

@app.route('/api/network/top-domains')
def get_top_domains():
    """Get network-wide top domains and trackers"""
    conn = get_db()
    cursor = conn.cursor()
    
    since = int((datetime.now() - timedelta(hours=24)).timestamp())
    
    # Get top domains (all queries)
    cursor.execute("""
        SELECT domain, COUNT(*) as count
        FROM dns_queries
        WHERE timestamp > ?
        GROUP BY domain
        ORDER BY count DESC
        LIMIT 30
    """, (since,))
    
    top_domains = [{'domain': row[0], 'count': row[1]} for row in cursor.fetchall()]
    
    # Get top tracker domains
    cursor.execute("""
        SELECT domain, COUNT(*) as count
        FROM dns_queries
        WHERE is_tracker = 1 AND timestamp > ?
        GROUP BY domain
        ORDER BY count DESC
        LIMIT 30
    """, (since,))
    
    top_trackers = [{'domain': row[0], 'count': row[1]} for row in cursor.fetchall()]
    
    conn.close()
    
    return jsonify({
        'top_domains': top_domains,
        'top_trackers': top_trackers
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=False)

