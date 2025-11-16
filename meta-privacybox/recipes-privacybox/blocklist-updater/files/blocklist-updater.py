#!/usr/bin/env python3
"""
Blocklist Updater - Downloads and processes tracker blocklists
"""

import urllib.request
import re
import subprocess
from pathlib import Path

BLOCKLIST_DIR = "/etc/privacy-box"
BLOCKLIST_FILE = f"{BLOCKLIST_DIR}/blocklist.txt"

# Blocklist sources
BLOCKLISTS = [
    "https://raw.githubusercontent.com/StevenBlack/hosts/master/hosts",
    "https://raw.githubusercontent.com/AdguardTeam/AdguardFilters/master/MobileFilter/sections/adservers.txt",
    "https://easylist.to/easylist/easylist.txt",
    "https://easylist.to/easylist/easyprivacy.txt",
]

def download_blocklist(url):
    """Download a blocklist"""
    try:
        print(f"Downloading {url}...")
        with urllib.request.urlopen(url, timeout=30) as response:
            return response.read().decode('utf-8', errors='ignore')
    except Exception as e:
        print(f"Error downloading {url}: {e}")
        return None

def parse_hosts_format(content):
    """Parse hosts file format: IP domain"""
    domains = set()
    for line in content.split('\n'):
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        parts = line.split()
        if len(parts) >= 2:
            # Usually format: 0.0.0.0 domain.com
            domain = parts[1].strip()
            if domain and '.' in domain:
                domains.add(domain)
    return domains

def parse_adblock_format(content):
    """Parse AdBlock format: ||domain.com^"""
    domains = set()
    for line in content.split('\n'):
        line = line.strip()
        if not line or line.startswith('!'):
            continue
        # Match ||domain.com^ or ||domain.com^$third-party
        match = re.match(r'\|\|([^/^$]+)', line)
        if match:
            domain = match.group(1).strip()
            if domain and '.' in domain:
                domains.add(domain)
    return domains

def update_blocklist():
    """Download and merge all blocklists"""
    all_domains = set()
    
    for url in BLOCKLISTS:
        content = download_blocklist(url)
        if not content:
            continue
            
        # Try to detect format and parse
        if '||' in content[:1000]:  # AdBlock format
            domains = parse_adblock_format(content)
        else:  # Hosts format
            domains = parse_hosts_format(content)
            
        all_domains.update(domains)
        print(f"  Found {len(domains)} domains")
    
    # Write combined blocklist
    Path(BLOCKLIST_DIR).mkdir(parents=True, exist_ok=True)
    
    with open(BLOCKLIST_FILE, 'w') as f:
        for domain in sorted(all_domains):
            f.write(f"0.0.0.0 {domain}\n")
    
    print(f"\nTotal unique domains: {len(all_domains)}")
    print(f"Blocklist written to {BLOCKLIST_FILE}")
    
    # Reload dnsmasq
    try:
        subprocess.run(['systemctl', 'reload', 'dnsmasq'], check=True)
        print("dnsmasq reloaded")
    except Exception as e:
        print(f"Warning: Could not reload dnsmasq: {e}")

if __name__ == "__main__":
    update_blocklist()


