#!/usr/bin/env python3
"""
MAC OUI Vendor Lookup
Uses local IEEE OUI database file for offline vendor detection
"""

import os
import re
from pathlib import Path

OUI_DB_PATH = "/usr/share/device-tracker/oui-database.txt"
FALLBACK_OUI_DB = "/etc/device-tracker/oui-database.txt"

def _get_script_dir_db():
    """Get OUI database path in same directory as script (for development)"""
    try:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        return os.path.join(script_dir, "oui-database.txt")
    except:
        return None

class OUILookup:
    def __init__(self):
        self.oui_cache = {}
        self.db_path = None
        self._load_database()
    
    def _load_database(self):
        """Load OUI database from file"""
        # Try all possible locations
        script_dir_db = _get_script_dir_db()
        search_paths = [OUI_DB_PATH, FALLBACK_OUI_DB]
        if script_dir_db and os.path.exists(script_dir_db):
            search_paths.insert(0, script_dir_db)
        
        for path in search_paths:
            if os.path.exists(path):
                self.db_path = path
                self._parse_database(path)
                print(f"Loaded OUI database from {path} ({len(self.oui_cache)} entries)")
                return
        
        # If no database file exists, use empty cache
        print(f"Warning: OUI database not found. Tried: {', '.join(search_paths)}")
        self.oui_cache = {}
    
    def _parse_database(self, db_path):
        """Parse OUI database file"""
        try:
            with open(db_path, 'r', encoding='utf-8', errors='ignore') as f:
                for line in f:
                    line = line.strip()
                    # Skip comments and empty lines
                    if not line or line.startswith('#'):
                        continue
                    
                    # Format: OUI_PREFIX|VENDOR_NAME or OUI_PREFIX\tVENDOR_NAME
                    parts = re.split(r'[|\t]', line, 1)
                    if len(parts) == 2:
                        oui_prefix = parts[0].strip().upper().replace(':', '').replace('-', '')
                        vendor_name = parts[1].strip()
                        if len(oui_prefix) == 6:  # Valid OUI prefix
                            self.oui_cache[oui_prefix] = vendor_name
        except Exception as e:
            print(f"Error parsing OUI database: {e}")
            self.oui_cache = {}
    
    def lookup(self, mac_address):
        """Lookup vendor name from MAC address"""
        if not mac_address or mac_address == 'unknown':
            return None
        
        # Normalize MAC address
        mac_clean = mac_address.upper().replace(':', '').replace('-', '')
        
        # Extract OUI prefix (first 6 hex characters)
        if len(mac_clean) >= 6:
            oui_prefix = mac_clean[:6]
            return self.oui_cache.get(oui_prefix)
        
        return None
    
    def get_vendor(self, mac_address):
        """Get vendor name, returns None if not found"""
        return self.lookup(mac_address)

# Global instance
_oui_lookup = None

def get_oui_lookup():
    """Get singleton OUI lookup instance"""
    global _oui_lookup
    if _oui_lookup is None:
        _oui_lookup = OUILookup()
    return _oui_lookup

def lookup_vendor(mac_address):
    """Convenience function to lookup vendor"""
    lookup = get_oui_lookup()
    return lookup.lookup(mac_address)

