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

def calculate_privacy_score(total_queries, tracker_queries, blocked_queries):
    """Calculate privacy score (0-100) based on tracker ratio and blocking effectiveness"""
    if total_queries == 0:
        return 100  # No queries = perfect privacy
    
    # Tracker ratio (lower is better)
    tracker_ratio = tracker_queries / total_queries if total_queries > 0 else 0
    
    # Blocking effectiveness (higher is better)
    blocking_ratio = blocked_queries / tracker_queries if tracker_queries > 0 else 1.0
    
    # Base score starts at 100
    score = 100
    
    # Penalize for tracker ratio (0% trackers = no penalty, 100% trackers = -50 points)
    tracker_penalty = tracker_ratio * 50
    score -= tracker_penalty
    
    # Reward for blocking effectiveness (100% blocked = +20 points, 0% blocked = 0 points)
    blocking_bonus = blocking_ratio * 20
    score += blocking_bonus
    
    # Ensure score is between 0 and 100
    score = max(0, min(100, score))
    
    return round(score)

def get_privacy_score_color(score):
    """Get color class for privacy score"""
    if score >= 80:
        return 'privacy-excellent'
    elif score >= 60:
        return 'privacy-good'
    elif score >= 40:
        return 'privacy-moderate'
    else:
        return 'privacy-poor'

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
    total_queries = stats[0] or 0
    tracker_queries = stats[1] or 0
    blocked_queries = stats[2] or 0
    device_count = stats[3] or 0
    
    # Calculate network privacy score
    network_privacy_score = calculate_privacy_score(total_queries, tracker_queries, blocked_queries)
    network_privacy_color = get_privacy_score_color(network_privacy_score)
    
    # Get per-device breakdown
    cursor.execute("""
        SELECT 
            device_ip,
            COUNT(*) as queries,
            SUM(CASE WHEN is_tracker = 1 THEN 1 ELSE 0 END) as trackers,
            SUM(CASE WHEN blocked = 1 THEN 1 ELSE 0 END) as blocked
        FROM dns_queries
        WHERE timestamp > ?
        GROUP BY device_ip
        ORDER BY trackers DESC
    """, (since,))
    
    devices = []
    for row in cursor.fetchall():
        device_ip = row[0]
        device_queries = row[1]
        device_trackers = row[2]
        device_blocked = row[3]
        
        # Get most up-to-date device name
        device_name = get_device_name(cursor, device_ip)
        device_type = get_device_type(device_name)
        device_icon = get_device_icon(device_type)
        
        # Calculate per-device privacy score
        device_privacy_score = calculate_privacy_score(device_queries, device_trackers, device_blocked)
        device_privacy_color = get_privacy_score_color(device_privacy_score)
        
        devices.append({
            'ip': device_ip,
            'name': device_name,
            'type': device_type,
            'icon': device_icon,
            'queries': device_queries,
            'trackers': device_trackers,
            'privacy_score': device_privacy_score,
            'privacy_color': device_privacy_color
        })
    
    conn.close()
    
    return jsonify({
        'network': {
            'total_queries': total_queries,
            'tracker_queries': tracker_queries,
            'blocked_queries': blocked_queries,
            'device_count': device_count,
            'privacy_score': network_privacy_score,
            'privacy_color': network_privacy_color
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

@app.route('/api/geolocation/stats')
def get_geolocation_stats():
    """Get geolocation statistics"""
    conn = get_db()
    cursor = conn.cursor()
    
    since = int((datetime.now() - timedelta(hours=24)).timestamp())
    
    # Get country breakdown
    cursor.execute("""
        SELECT 
            country_code,
            COUNT(*) as query_count,
            SUM(CASE WHEN is_tracker = 1 THEN 1 ELSE 0 END) as tracker_count
        FROM dns_queries
        WHERE timestamp > ? AND country_code IS NOT NULL
        GROUP BY country_code
        ORDER BY query_count DESC
    """, (since,))
    
    countries = []
    for row in cursor.fetchall():
        countries.append({
            'country_code': row[0],
            'queries': row[1],
            'trackers': row[2]
        })
    
    # Get total queries with country data
    cursor.execute("""
        SELECT COUNT(*) 
        FROM dns_queries 
        WHERE timestamp > ? AND country_code IS NOT NULL
    """, (since,))
    total_with_country = cursor.fetchone()[0] or 0
    
    # Get total queries
    cursor.execute("""
        SELECT COUNT(*) 
        FROM dns_queries 
        WHERE timestamp > ?
    """, (since,))
    total_queries = cursor.fetchone()[0] or 0
    
    conn.close()
    
    return jsonify({
        'countries': countries,
        'total_queries': total_queries,
        'queries_with_country': total_with_country,
        'coverage_percent': round((total_with_country / total_queries * 100) if total_queries > 0 else 0, 1)
    })

@app.route('/api/geolocation/countries')
def get_geolocation_countries():
    """Get list of countries with query statistics"""
    conn = get_db()
    cursor = conn.cursor()
    
    since = int((datetime.now() - timedelta(hours=24)).timestamp())
    
    cursor.execute("""
        SELECT 
            country_code,
            COUNT(*) as query_count,
            SUM(CASE WHEN is_tracker = 1 THEN 1 ELSE 0 END) as tracker_count,
            COUNT(DISTINCT device_ip) as device_count
        FROM dns_queries
        WHERE timestamp > ? AND country_code IS NOT NULL
        GROUP BY country_code
        ORDER BY query_count DESC
        LIMIT 50
    """, (since,))
    
    countries = []
    for row in cursor.fetchall():
        countries.append({
            'country_code': row[0],
            'queries': row[1],
            'trackers': row[2],
            'device_count': row[3]
        })
    
    conn.close()
    
    return jsonify(countries)

@app.route('/api/network/top-domains')
def get_top_domains():
    """Get network-wide top domains and trackers with device breakdown"""
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
    
    top_domains_raw = cursor.fetchall()
    top_domains = []
    
    # For each domain, get device breakdown
    for row in top_domains_raw:
        domain = row[0]
        total_count = row[1]
        
        # Get devices that queried this domain
        cursor.execute("""
            SELECT device_ip, COUNT(*) as device_count
            FROM dns_queries
            WHERE domain = ? AND timestamp > ?
            GROUP BY device_ip
            ORDER BY device_count DESC
        """, (domain, since))
        
        devices = []
        for device_row in cursor.fetchall():
            device_ip = device_row[0]
            device_count = device_row[1]
            device_name = get_device_name(cursor, device_ip)
            device_type = get_device_type(device_name)
            device_icon = get_device_icon(device_type)
            
            devices.append({
                'ip': device_ip,
                'name': device_name,
                'type': device_type,
                'icon': device_icon,
                'count': device_count
            })
        
        top_domains.append({
            'domain': domain,
            'count': total_count,
            'devices': devices
        })
    
    # Get top tracker domains
    cursor.execute("""
        SELECT domain, COUNT(*) as count
        FROM dns_queries
        WHERE is_tracker = 1 AND timestamp > ?
        GROUP BY domain
        ORDER BY count DESC
        LIMIT 30
    """, (since,))
    
    top_trackers_raw = cursor.fetchall()
    top_trackers = []
    
    # For each tracker domain, get device breakdown
    for row in top_trackers_raw:
        domain = row[0]
        total_count = row[1]
        
        # Get devices that queried this tracker domain
        cursor.execute("""
            SELECT device_ip, COUNT(*) as device_count
            FROM dns_queries
            WHERE domain = ? AND is_tracker = 1 AND timestamp > ?
            GROUP BY device_ip
            ORDER BY device_count DESC
        """, (domain, since))
        
        devices = []
        for device_row in cursor.fetchall():
            device_ip = device_row[0]
            device_count = device_row[1]
            device_name = get_device_name(cursor, device_ip)
            device_type = get_device_type(device_name)
            device_icon = get_device_icon(device_type)
            
            devices.append({
                'ip': device_ip,
                'name': device_name,
                'type': device_type,
                'icon': device_icon,
                'count': device_count
            })
        
        top_trackers.append({
            'domain': domain,
            'count': total_count,
            'devices': devices
        })
    
    conn.close()
    
    return jsonify({
        'top_domains': top_domains,
        'top_trackers': top_trackers
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=False)

