#!/usr/bin/env python3
"""
Device Tracker - Correlates DNS queries with devices
Reads dnsmasq logs and DHCP leases to attribute queries to devices
"""

import re
import sqlite3
import json
import time
import subprocess
import sys
import os
from datetime import datetime
from pathlib import Path
from collections import defaultdict

# Add oui_lookup to path - try multiple locations
try:
    # Try to get script directory
    _script_file = __file__ if '__file__' in globals() else sys.argv[0] if sys.argv else '.'
    _script_dir = os.path.dirname(os.path.abspath(_script_file))
    sys.path.insert(0, _script_dir)
except:
    pass

# Also add /usr/bin where oui_lookup.py will be installed
sys.path.insert(0, '/usr/bin')

try:
    from oui_lookup import lookup_vendor
    OUI_AVAILABLE = True
except ImportError as e:
    OUI_AVAILABLE = False
    print(f"Warning: oui_lookup module not available ({e}), using fallback vendor detection")

DNSMASQ_LOG = "/var/log/pihole/pihole.log"
DHCP_LEASES = "/var/lib/misc/dnsmasq.leases"  # dnsmasq default lease file
DB_PATH = "/var/lib/device-tracker/device_tracker.db"
TRACKER_DB = "/var/lib/device-tracker/trackers.db"

class DeviceTracker:
    def __init__(self):
        self.db = sqlite3.connect(DB_PATH)
        self.init_db()
        self.device_cache = {}
        self.load_dhcp_leases()
        # Update any Unknown devices on startup
        self.update_unknown_devices()
        
    def init_db(self):
        """Initialize SQLite database"""
        cursor = self.db.cursor()
        # Tables
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS dns_queries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp INTEGER,
                device_ip TEXT,
                device_mac TEXT,
                device_name TEXT,
                domain TEXT,
                is_tracker INTEGER DEFAULT 0,
                blocked INTEGER DEFAULT 0
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS devices (
                ip TEXT PRIMARY KEY,
                mac TEXT,
                name TEXT,
                first_seen INTEGER,
                last_seen INTEGER
            )
        """)
        # Indexes (each in its own statement; sqlite3 doesn't allow multiple)
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_device_ip "
            "ON dns_queries(device_ip)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_domain "
            "ON dns_queries(domain)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_timestamp "
            "ON dns_queries(timestamp)"
        )
        self.db.commit()
        
    def load_dhcp_leases(self):
        """Load DHCP lease file to map IP to MAC and hostname"""
        # dnsmasq uses simple format: timestamp mac ip hostname
        if Path(DHCP_LEASES).exists():
            self.parse_dnsmasq_leases(DHCP_LEASES)
        else:
            # Try alternative locations
            alt_locations = [
                "/var/lib/dhcp/dhcpd.leases",
                "/var/lib/dhcpcd5/dhcpcd.leases"
            ]
            for alt_path in alt_locations:
                if Path(alt_path).exists():
                    self.parse_dnsmasq_leases(alt_path)
                    break
                        
    def parse_dnsmasq_leases(self, lease_file):
        """Parse dnsmasq lease format: timestamp mac ip hostname"""
        try:
            with open(lease_file, 'r') as f:
                for line in f:
                    parts = line.strip().split()
                    if len(parts) >= 3:
                        mac = parts[1]
                        ip = parts[2]
                        # Get hostname, or try reverse DNS, or use MAC-based name
                        hostname = parts[3] if len(parts) > 3 and parts[3] != '*' else None
                        if not hostname or hostname == 'Unknown':
                            hostname = self.resolve_device_name(ip, mac)
                        self.device_cache[ip] = {
                            'mac': mac,
                            'name': hostname
                        }
        except Exception as e:
            print(f"Error parsing leases: {e}")
    
    def resolve_device_name(self, ip, mac):
        """Try to resolve device name from various sources"""
        # Try reverse DNS first (with timeout)
        try:
            import socket
            socket.setdefaulttimeout(2)  # 2 second timeout
            hostname, _, _ = socket.gethostbyaddr(ip)
            if hostname and hostname != ip:
                name = hostname.split('.')[0]  # Remove domain
                if name and name != ip:
                    return name
        except:
            pass
        
        # Try MAC OUI lookup using database (only if we have a valid MAC)
        if mac and mac != 'unknown' and ':' in mac:
            if OUI_AVAILABLE:
                try:
                    vendor = lookup_vendor(mac)
                    if vendor and 'Unknown Vendor' not in vendor and 'Unknown' not in vendor:
                        # Clean up vendor name - remove common suffixes
                        vendor_clean = vendor.replace(' Inc.', '').replace(' Corporation', '').replace(' Inc', '')
                        vendor_clean = vendor_clean.replace(' Technologies', '').replace(' Electronics', '')
                        return f"{vendor_clean} Device"
                except Exception as e:
                    print(f"Error in OUI lookup: {e}")
            
            # Fallback to hardcoded map for common devices (if OUI lookup fails)
            # This is only used if OUI database is not available
            mac_prefix = mac.upper().replace(':', '')[:6]
            fallback_map = {
                '80482C': 'Wyze',
                '0417B6': 'Eufy',
                'E86538': 'Microsoft',
            }
            if mac_prefix in fallback_map:
                return f"{fallback_map[mac_prefix]} Device"
        
        # Fallback: Use last octet of IP
        return f"Device-{ip.split('.')[-1]}"
            
    def get_device_info(self, ip):
        """Get device info from cache, database, or ARP table"""
        # First check cache
        if ip in self.device_cache:
            return self.device_cache[ip]
            
        # Try database
        cursor = self.db.cursor()
        cursor.execute("SELECT mac, name FROM devices WHERE ip = ?", (ip,))
        row = cursor.fetchone()
        if row and row[0] != 'unknown':
            return {'mac': row[0], 'name': row[1]}
        
        # Try ARP table to get MAC address
        mac = self.get_mac_from_arp(ip)
        if mac and mac != 'unknown':
            # Resolve name from MAC
            name = self.resolve_device_name(ip, mac)
            # Cache it
            self.device_cache[ip] = {'mac': mac, 'name': name}
            return {'mac': mac, 'name': name}
            
        # Last resort: try to resolve name from IP only
        name = self.resolve_device_name(ip, 'unknown')
        return {'mac': 'unknown', 'name': name}
    
    def get_mac_from_arp(self, ip):
        """Get MAC address from ARP table"""
        try:
            # Read /proc/net/arp
            with open('/proc/net/arp', 'r') as f:
                for line in f:
                    parts = line.split()
                    if len(parts) >= 4 and parts[0] == ip:
                        mac = parts[3]
                        if mac != '00:00:00:00:00:00':
                            return mac
        except Exception as e:
            print(f"Error reading ARP table: {e}")
        
        # Try ip neigh command as fallback
        try:
            result = subprocess.run(['ip', 'neigh', 'show', ip], 
                                  capture_output=True, text=True, timeout=2)
            if result.returncode == 0 and result.stdout:
                parts = result.stdout.strip().split()
                if len(parts) >= 5:
                    mac = parts[4]
                    if mac and mac != '00:00:00:00:00:00':
                        return mac
        except Exception as e:
            pass
        
        return 'unknown'
    
    def update_unknown_devices(self):
        """Update all Unknown device entries with resolved names"""
        cursor = self.db.cursor()
        # Get all devices with Unknown names
        cursor.execute("SELECT ip FROM devices WHERE name = 'Unknown' OR name IS NULL")
        unknown_ips = [row[0] for row in cursor.fetchall()]
        
        if not unknown_ips:
            return
        
        print(f"Updating {len(unknown_ips)} devices with Unknown names...")
        updated_count = 0
        
        for ip in unknown_ips:
            mac = self.get_mac_from_arp(ip)
            name = self.resolve_device_name(ip, mac)
            
            # Update devices table
            cursor.execute("UPDATE devices SET mac = ?, name = ? WHERE ip = ?", 
                          (mac, name, ip))
            
            # Update recent dns_queries (last 7 days) where device_name is Unknown
            since = int(time.time()) - (7 * 24 * 60 * 60)
            cursor.execute("""
                UPDATE dns_queries 
                SET device_mac = ?, device_name = ? 
                WHERE device_ip = ? AND (device_name = 'Unknown' OR device_name IS NULL) 
                AND timestamp > ?
            """, (mac, name, ip, since))
            
            updated_count += 1
            if updated_count % 5 == 0:
                print(f"  Updated {updated_count}/{len(unknown_ips)} devices...")
        
        self.db.commit()
        print(f"✓ Updated {updated_count} devices with resolved names")
        
    def is_tracker_domain(self, domain):
        """Check if domain is a known tracker"""
        # Simple check - in production, use proper tracker database
        tracker_keywords = ['ad', 'ads', 'track', 'tracking', 'analytics', 
                          'doubleclick', 'google-analytics', 'facebook.com',
                          'googletagmanager', 'scorecardresearch']
        domain_lower = domain.lower()
        return any(keyword in domain_lower for keyword in tracker_keywords)
        
    def parse_dnsmasq_log(self):
        """Parse dnsmasq log file for DNS queries"""
        # Wait for log file to exist (dnsmasq may create it on first query)
        log_path = Path(DNSMASQ_LOG)
        log_dir = log_path.parent
        
        # Ensure log directory exists
        if not log_dir.exists():
            log_dir.mkdir(parents=True, exist_ok=True)
            # Create empty log file if it doesn't exist
            if not log_path.exists():
                log_path.touch()
        
        # Wait for log file to exist (with timeout)
        max_wait = 60  # Wait up to 60 seconds
        waited = 0
        while not log_path.exists() and waited < max_wait:
            time.sleep(1)
            waited += 1
            if waited % 10 == 0:
                print(f"Waiting for log file {DNSMASQ_LOG}... ({waited}s)")
        
        if not log_path.exists():
            print(f"ERROR: Log file {DNSMASQ_LOG} does not exist after {max_wait}s")
            return
            
        try:
            with open(DNSMASQ_LOG, 'r') as f:
                # Start reading from beginning to catch existing entries
                # On subsequent reads, we'll get new lines as they're appended
                while True:
                    line = f.readline()
                    if not line:
                        time.sleep(1)
                        continue
                        
                    # Parse dnsmasq log format
                    # query[A] example.com from 192.168.1.100
                    match = re.search(r'query\[.*?\] (\S+) from (\S+)', line)
                    if match:
                        domain = match.group(1)
                        client_ip = match.group(2)
                        
                        device_info = self.get_device_info(client_ip)
                        
                        # Check if blocked
                        blocked = 'is 0.0.0.0' in line or 'is NXDOMAIN' in line
                        is_tracker = self.is_tracker_domain(domain)
                        
                        # Store in database
                        cursor = self.db.cursor()
                        cursor.execute("""
                            INSERT INTO dns_queries 
                            (timestamp, device_ip, device_mac, device_name, domain, is_tracker, blocked)
                            VALUES (?, ?, ?, ?, ?, ?, ?)
                        """, (
                            int(time.time()),
                            client_ip,
                            device_info['mac'],
                            device_info['name'],
                            domain,
                            1 if is_tracker else 0,
                            1 if blocked else 0
                        ))
                        
                        # Update device info
                        cursor.execute("""
                            INSERT OR REPLACE INTO devices (ip, mac, name, last_seen)
                            VALUES (?, ?, ?, ?)
                        """, (client_ip, device_info['mac'], device_info['name'], int(time.time())))
                        
                        self.db.commit()
                        
        except KeyboardInterrupt:
            pass
        except Exception as e:
            print(f"Error parsing log: {e}")
            
    def run(self):
        """Main loop"""
        print("Device Tracker starting...")
        self.parse_dnsmasq_log()

if __name__ == "__main__":
    tracker = DeviceTracker()
    tracker.run()

