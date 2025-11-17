#!/usr/bin/env python3
"""
Geolocation Service - Resolves domains to IPs and looks up countries
Uses IP2Location DB3 Lite database with caching
"""

import socket
import sqlite3
import os
import sys
import time
from pathlib import Path

# Try to import maxminddb (for GeoLite2)
try:
    import maxminddb
    MAXMIND_AVAILABLE = True
except ImportError:
    MAXMIND_AVAILABLE = False
    print("Warning: maxminddb library not available. Geolocation disabled.")

# Database paths
DB_PATH = "/var/lib/device-tracker/device_tracker.db"
GEOLITE2_DB = "/usr/share/device-tracker/GeoLite2-Country.mmdb"
FALLBACK_GEOLITE2_DB = "/etc/device-tracker/GeoLite2-Country.mmdb"

# Cache for domain -> IP -> Country lookups
_domain_ip_cache = {}
_ip_country_cache = {}
_geo_db = None

def get_geo_db():
    """Get GeoLite2 database reader instance (singleton)"""
    global _geo_db
    
    if not MAXMIND_AVAILABLE:
        return None
    
    if _geo_db is not None:
        return _geo_db
    
    # Try to find database file
    db_path = None
    for path in [GEOLITE2_DB, FALLBACK_GEOLITE2_DB]:
        if os.path.exists(path):
            db_path = path
            break
    
    if not db_path:
        print(f"Warning: GeoLite2 database not found. Tried: {GEOLITE2_DB}, {FALLBACK_GEOLITE2_DB}")
        return None
    
    try:
        _geo_db = maxminddb.open_database(db_path)
        print(f"Loaded GeoLite2 database from {db_path}")
        return _geo_db
    except Exception as e:
        print(f"Error loading GeoLite2 database: {e}")
        return None

def resolve_domain_to_ip(domain):
    """Resolve domain to IP address with caching"""
    # Skip common CDN/cloud domains that aren't country-specific
    cdn_domains = ['cloudflare.com', 'cloudfront.net', 'fastly.com', 'akamai.net', 
                   'cdn', 'edge', 'static', 'assets']
    domain_lower = domain.lower()
    if any(cdn in domain_lower for cdn in cdn_domains):
        return None  # Skip CDN domains
    
    # Check cache first
    if domain in _domain_ip_cache:
        return _domain_ip_cache[domain]
    
    try:
        # Resolve domain to IP
        ip = socket.gethostbyname(domain)
        _domain_ip_cache[domain] = ip
        return ip
    except (socket.gaierror, socket.herror, OSError):
        # Domain resolution failed
        _domain_ip_cache[domain] = None
        return None

def lookup_country_from_ip(ip):
    """Lookup country code from IP address with caching"""
    if not ip:
        return None
    
    # Check cache first
    if ip in _ip_country_cache:
        return _ip_country_cache[ip]
    
    geo_db = get_geo_db()
    if not geo_db:
        return None
    
    try:
        record = geo_db.get(ip)
        # GeoLite2-Country format: record['country']['iso_code']
        country_code = None
        if record and 'country' in record and 'iso_code' in record['country']:
            country_code = record['country']['iso_code']
        _ip_country_cache[ip] = country_code
        return country_code
    except Exception as e:
        print(f"Error looking up country for IP {ip}: {e}")
        _ip_country_cache[ip] = None
        return None

def get_country_for_domain(domain):
    """Get country code for a domain (with caching)"""
    # Resolve domain to IP
    ip = resolve_domain_to_ip(domain)
    if not ip:
        return None
    
    # Lookup country from IP
    country = lookup_country_from_ip(ip)
    return country

def get_country_from_cache(domain, db_cursor):
    """Get country code from database cache, or resolve if not cached"""
    if not MAXMIND_AVAILABLE:
        return None
    
    # First check database cache
    db_cursor.execute("""
        SELECT country_code 
        FROM domain_country_cache 
        WHERE domain = ?
    """, (domain,))
    row = db_cursor.fetchone()
    if row and row[0]:
        return row[0]
    
    # Not in cache, resolve it
    country = get_country_for_domain(domain)
    
    # Cache in database for future use
    if country:
        try:
            db_cursor.execute("""
                INSERT OR REPLACE INTO domain_country_cache (domain, country_code, last_updated)
                VALUES (?, ?, ?)
            """, (domain, country, int(time.time())))
            db_cursor.connection.commit()
        except Exception as e:
            print(f"Error caching country for domain {domain}: {e}")
    
    return country

def init_geolocation_cache_table(db_cursor):
    """Initialize domain_country_cache table if it doesn't exist"""
    db_cursor.execute("""
        CREATE TABLE IF NOT EXISTS domain_country_cache (
            domain TEXT PRIMARY KEY,
            country_code TEXT,
            last_updated INTEGER
        )
    """)
    db_cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_domain_country_cache_domain 
        ON domain_country_cache(domain)
    """)
    db_cursor.connection.commit()

