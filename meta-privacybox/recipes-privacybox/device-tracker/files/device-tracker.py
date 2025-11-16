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
from datetime import datetime
from pathlib import Path
from collections import defaultdict

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
                        hostname = parts[3] if len(parts) > 3 else 'Unknown'
                        self.device_cache[ip] = {
                            'mac': mac,
                            'name': hostname
                        }
        except Exception as e:
            print(f"Error parsing leases: {e}")
            
    def get_device_info(self, ip):
        """Get device info from cache or database"""
        if ip in self.device_cache:
            return self.device_cache[ip]
            
        # Try database
        cursor = self.db.cursor()
        cursor.execute("SELECT mac, name FROM devices WHERE ip = ?", (ip,))
        row = cursor.fetchone()
        if row:
            return {'mac': row[0], 'name': row[1]}
            
        return {'mac': 'unknown', 'name': 'Unknown'}
        
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

