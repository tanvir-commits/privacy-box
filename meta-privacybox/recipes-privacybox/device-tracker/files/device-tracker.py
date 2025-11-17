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
                        
    def extract_device_type_from_hostname(self, hostname):
        """Extract device type from DHCP hostname (e.g., 'John's iPhone' -> 'iPhone')"""
        if not hostname or hostname == '*' or hostname == 'Unknown':
            return None
        
        hostname_lower = hostname.lower()
        
        # Apple devices
        if 'iphone' in hostname_lower:
            return 'iPhone'
        if 'ipad' in hostname_lower:
            return 'iPad'
        if 'ipod' in hostname_lower:
            return 'iPod'
        if 'apple' in hostname_lower and ('device' in hostname_lower or 'mac' in hostname_lower):
            return 'Apple Device'
        
        # Android devices
        if 'android' in hostname_lower:
            if 'tablet' in hostname_lower:
                return 'Android Tablet'
            return 'Android Device'
        if any(brand in hostname_lower for brand in ['samsung', 'pixel', 'oneplus', 'xiaomi', 'huawei', 'oppo', 'vivo']):
            return 'Android Device'
        
        # Windows devices
        if 'windows' in hostname_lower:
            if 'laptop' in hostname_lower or 'notebook' in hostname_lower:
                return 'Windows Laptop'
            if 'desktop' in hostname_lower or 'pc' in hostname_lower:
                return 'Windows PC'
            return 'Windows Device'
        if 'pc' in hostname_lower or 'desktop' in hostname_lower or 'laptop' in hostname_lower:
            return 'Windows Device'
        
        return None
    
    def parse_dnsmasq_leases(self, lease_file):
        """Parse dnsmasq lease format: timestamp mac ip hostname"""
        try:
            with open(lease_file, 'r') as f:
                for line in f:
                    parts = line.strip().split()
                    if len(parts) >= 3:
                        mac = parts[1]
                        ip = parts[2]
                        # Get hostname from DHCP lease
                        hostname = parts[3] if len(parts) > 3 and parts[3] != '*' else None
                        
                        # First, try to extract device type from hostname (professional approach)
                        device_type = self.extract_device_type_from_hostname(hostname)
                        if device_type:
                            # Use device type from hostname
                            self.device_cache[ip] = {
                                'mac': mac,
                                'name': device_type
                            }
                        elif hostname and hostname != 'Unknown':
                            # Use hostname as-is if it exists but doesn't contain device type
                            self.device_cache[ip] = {
                                'mac': mac,
                                'name': hostname
                            }
                        else:
                            # Fallback to resolve_device_name (DNS patterns, OUI, etc.)
                            resolved_name = self.resolve_device_name(ip, mac)
                            self.device_cache[ip] = {
                                'mac': mac,
                                'name': resolved_name
                            }
        except Exception as e:
            print(f"Error parsing leases: {e}")
    
    def detect_device_from_dns_patterns(self, ip, cursor):
        """Detect device type from DNS query patterns (works even with randomized MACs)"""
        since = int(time.time()) - (7 * 24 * 60 * 60)  # Last 7 days
        
        # Apple device detection
        apple_domains = ['icloud.com', 'apple-dns.net', 'apple.com', 'appleid.apple.com', 
                        'apple-cloudkit.com', 'mzstatic.com', 'apple-mapkit.com']
        total_apple_queries = 0
        for domain in apple_domains:
            cursor.execute("""
                SELECT COUNT(*) FROM dns_queries 
                WHERE device_ip = ? AND domain LIKE ? AND timestamp > ?
            """, (ip, f'%{domain}%', since))
            count = cursor.fetchone()[0]
            total_apple_queries += count
        
        if total_apple_queries >= 5:
            cursor.execute("""
                SELECT COUNT(*) FROM dns_queries 
                WHERE device_ip = ? AND timestamp > ?
            """, (ip, since))
            total_queries = cursor.fetchone()[0]
            
            if total_apple_queries > 100:  # High Apple query volume = iPhone
                return "iPhone"
            elif total_apple_queries >= 5 and total_queries < 200:  # Moderate Apple queries, low total = iPad
                return "iPad"
            else:
                return "Apple Device"
        
        # Android device detection
        android_domains = ['android.googleapis.com', 'gstatic.com', 'googleapis.com', 
                          'google.com', 'android.com', 'googletagmanager.com', 'gmail.com',
                          'googleusercontent.com', 'googleplay.com', 'android.clients.google.com']
        total_android_queries = 0
        for domain in android_domains:
            cursor.execute("""
                SELECT COUNT(*) FROM dns_queries 
                WHERE device_ip = ? AND domain LIKE ? AND timestamp > ?
            """, (ip, f'%{domain}%', since))
            count = cursor.fetchone()[0]
            total_android_queries += count
        
        if total_android_queries >= 5:
            cursor.execute("""
                SELECT COUNT(*) FROM dns_queries 
                WHERE device_ip = ? AND timestamp > ?
            """, (ip, since))
            total_queries = cursor.fetchone()[0]
            
            # Android phones typically have higher query volume than tablets
            if total_android_queries > 50 and total_queries > 300:
                return "Android Phone"
            elif total_android_queries >= 5 and total_queries < 200:
                return "Android Tablet"
            else:
                return "Android Device"
        
        # Windows device detection
        windows_domains = ['microsoft.com', 'windowsupdate.com', 'microsoftonline.com', 
                          'live.com', 'outlook.com', 'office.com', 'office365.com',
                          'microsoftedge.com', 'bing.com', 'onedrive.com', 'skype.com']
        total_windows_queries = 0
        for domain in windows_domains:
            cursor.execute("""
                SELECT COUNT(*) FROM dns_queries 
                WHERE device_ip = ? AND domain LIKE ? AND timestamp > ?
            """, (ip, f'%{domain}%', since))
            count = cursor.fetchone()[0]
            total_windows_queries += count
        
        if total_windows_queries >= 5:
            cursor.execute("""
                SELECT COUNT(*) FROM dns_queries 
                WHERE device_ip = ? AND timestamp > ?
            """, (ip, since))
            total_queries = cursor.fetchone()[0]
            
            # Windows devices typically have high query volume
            if total_windows_queries > 30 and total_queries > 500:
                return "Windows PC"
            elif total_windows_queries >= 5:
                return "Windows Device"
        
        return None
    
    def resolve_device_name(self, ip, mac):
        """Try to resolve device name from various sources"""
        # Priority 1: Check DHCP hostname (if available in cache)
        if ip in self.device_cache:
            cached_name = self.device_cache[ip].get('name')
            # If cached name is a device type, use it
            if cached_name and any(keyword in cached_name.lower() for keyword in 
                                  ['iphone', 'ipad', 'ipod', 'apple', 'android', 'windows', 'pc', 'laptop']):
                return cached_name
        
        # Priority 2: Check DNS query patterns to identify device type (works even with randomized MACs)
        cursor = self.db.cursor()
        dns_pattern_result = self.detect_device_from_dns_patterns(ip, cursor)
        if dns_pattern_result:
            return dns_pattern_result
        
        # Priority 3: Try reverse DNS (with timeout)
        try:
            import socket
            socket.setdefaulttimeout(2)  # 2 second timeout
            hostname, _, _ = socket.gethostbyaddr(ip)
            if hostname and hostname != ip:
                name = hostname.split('.')[0]  # Remove domain
                # Check for device type in hostname
                device_type = self.extract_device_type_from_hostname(name)
                if device_type:
                    return device_type
                # Check for device type names in hostname
                if any(keyword in name.lower() for keyword in ['iphone', 'ipad', 'ipod', 'apple', 'android', 'windows', 'pc', 'laptop']):
                    return name
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
        # First check cache (may contain DHCP hostname-based device type)
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
            # Resolve name (will check DNS patterns, OUI, etc.)
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
        """Update all Unknown/Device-XXX device entries with resolved names"""
        cursor = self.db.cursor()
        # Get all devices with Unknown names OR generic Device-XXX names (which need better identification)
        cursor.execute("""
            SELECT ip FROM devices 
            WHERE name = 'Unknown' OR name IS NULL 
               OR name LIKE 'Device-%'
        """)
        unknown_ips = [row[0] for row in cursor.fetchall()]
        
        if not unknown_ips:
            return
        
        print(f"Updating {len(unknown_ips)} devices with Unknown/Device-XXX names...")
        updated_count = 0
        
        for ip in unknown_ips:
            mac = self.get_mac_from_arp(ip)
            name = self.resolve_device_name(ip, mac)
            
            # Only update if we got a better name (not Device-XXX unless it was Unknown)
            current_name = cursor.execute("SELECT name FROM devices WHERE ip = ?", (ip,)).fetchone()
            current_name = current_name[0] if current_name else None
            
            # Update if name improved (Unknown -> anything, or Device-XXX -> named device)
            should_update = False
            if current_name in ('Unknown', None):
                should_update = True  # Always update Unknown
            elif current_name and current_name.startswith('Device-') and not name.startswith('Device-'):
                should_update = True  # Update Device-XXX to a real name
            elif current_name == name:
                should_update = False  # No change needed
            else:
                should_update = True  # Name changed
            
            if should_update:
                # Update devices table
                cursor.execute("UPDATE devices SET mac = ?, name = ? WHERE ip = ?", 
                              (mac, name, ip))
                
                # Update recent dns_queries (last 7 days) where device_name needs updating
                since = int(time.time()) - (7 * 24 * 60 * 60)
                cursor.execute("""
                    UPDATE dns_queries 
                    SET device_mac = ?, device_name = ? 
                    WHERE device_ip = ? 
                      AND (device_name = 'Unknown' OR device_name IS NULL OR device_name LIKE 'Device-%')
                      AND timestamp > ?
                """, (mac, name, ip, since))
                
                updated_count += 1
                if updated_count % 5 == 0:
                    print(f"  Updated {updated_count}/{len(unknown_ips)} devices...")
        
        if updated_count > 0:
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

