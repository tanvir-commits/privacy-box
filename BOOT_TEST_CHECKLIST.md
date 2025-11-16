# Privacy Box Boot Test Checklist

## Pre-Reboot State (Current)
- [x] All services running
- [x] Device database populated
- [x] Apple devices identified
- [x] Dashboard accessible
- [x] OUI database present (4,262 entries)

## Post-Reboot Verification

### 1. System Services
- [ ] device-tracker.service starts automatically
- [ ] privacy-dashboard.service starts automatically
- [ ] dnsmasq.service starts automatically
- [ ] sshd.service starts automatically
- [ ] All services are enabled (survive reboot)

### 2. Device Identification
- [ ] OUI database loads correctly (4,262 entries)
- [ ] DHCP hostname parsing works
- [ ] DNS pattern detection works
- [ ] Apple devices (iPhone/iPad) are identified correctly
- [ ] Device names persist after reboot

### 3. Dashboard Functionality
- [ ] Dashboard accessible at http://192.168.68.100:8080
- [ ] Device list displays correctly
- [ ] Device detail modal works
- [ ] Search functionality works
- [ ] Sort functionality works
- [ ] Network-wide top domains section works
- [ ] Real-time activity updates

### 4. Database & Data
- [ ] Device database persists (/var/lib/device-tracker/)
- [ ] DNS queries continue to be logged
- [ ] Device tracking continues to work
- [ ] No data loss after reboot

### 5. Network Services
- [ ] DHCP server (dnsmasq) works
- [ ] DNS server (dnsmasq) works
- [ ] SSH access works
- [ ] Network connectivity maintained

## Test Commands

```bash
# Check services
systemctl status device-tracker privacy-dashboard dnsmasq sshd

# Check device identification
python3 -c "import sqlite3; db=sqlite3.connect('/var/lib/device-tracker/device_tracker.db'); cursor=db.cursor(); cursor.execute('SELECT ip, name FROM devices WHERE name LIKE \"%Apple%\" OR name LIKE \"%iPhone%\" OR name LIKE \"%iPad%\"'); print('\n'.join([f'{ip} -> {name}' for ip, name in cursor.fetchall()]))"

# Check OUI database
wc -l /usr/share/device-tracker/oui-database.txt
# Should show: 4267 lines (4262 entries + 5 header lines)

# Test dashboard
curl http://localhost:8080/api/network/stats

# Check logs
journalctl -u device-tracker -n 20
journalctl -u privacy-dashboard -n 20
```

