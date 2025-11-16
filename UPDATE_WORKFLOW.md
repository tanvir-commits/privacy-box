# Privacy Box Update Workflows

This document describes different ways to update the Privacy Box system.

## 1. Quick File Updates via SSH

For rapid development and testing, update individual files without rebuilding the entire image.

### Using the update script:

```bash
cd /home/a/yocto/projects/privacy-box

# Update dashboard app
./update_via_ssh.sh privacy-dashboard/files/app.py

# Update dashboard HTML
./update_via_ssh.sh privacy-dashboard/files/templates/index.html

# Update device tracker
./update_via_ssh.sh device-tracker/files/device-tracker.py
```

### Manual SSH update:

```bash
# 1. Edit file locally
vim meta-privacybox/recipes-privacybox/privacy-dashboard/files/app.py

# 2. Copy to board
scp meta-privacybox/recipes-privacybox/privacy-dashboard/files/app.py \
    root@192.168.68.100:/usr/bin/privacy-dashboard

# 3. Restart service
ssh root@192.168.68.100 "systemctl restart privacy-dashboard"
```

## 2. Full Bundle Updates (RAUC OTA)

For production updates or when you need to update multiple components.

### Build bundle:

```bash
cd /home/a/yocto/builds/RAUC
source setup-environment frdm-imx93
bitbake core-image-minimal  # Build updated image
bitbake xoc-bundle           # Create RAUC bundle
```

### Install via SSH:

```bash
# Find bundle
BUNDLE=$(ls -t tmp/deploy/images/imx93frdm/xoc-bundle*.raucb | head -1)

# Copy to board
scp "$BUNDLE" root@192.168.68.100:/tmp/bundle.raucb

# Install update
ssh root@192.168.68.100 "rauc install /tmp/bundle.raucb"

# Check status
ssh root@192.168.68.100 "rauc status --detailed"

# After reboot, mark slot as good
ssh root@192.168.68.100 "rauc status mark-good"
```

### Install via HTTP server:

```bash
# On build machine, start HTTP server
cd /home/a/yocto/builds/RAUC/frdm-imx93/tmp/deploy/images/imx93frdm
python3 -m http.server 8000

# On board, install from server
ssh root@192.168.68.100 "rauc install http://192.168.68.100:8000/xoc-bundle-imx93frdm.raucb"
```

## 3. Development Workflow

### Iterative development:

1. **Make changes locally** in `meta-privacybox/recipes-privacybox/`
2. **Test via SSH** using `update_via_ssh.sh`
3. **Verify on board** at http://192.168.68.100:8080
4. **Commit changes** when working
5. **Build bundle** for final testing
6. **Tag release** when ready

### Example workflow:

```bash
# 1. Edit dashboard
vim meta-privacybox/recipes-privacybox/privacy-dashboard/files/app.py

# 2. Quick test
./update_via_ssh.sh privacy-dashboard/files/app.py

# 3. Check logs if needed
ssh root@192.168.68.100 "journalctl -u privacy-dashboard -f"

# 4. When satisfied, commit
git add meta-privacybox/recipes-privacybox/privacy-dashboard/
git commit -m "Improve dashboard API response time"

# 5. Build and test full bundle
cd /home/a/yocto/builds/RAUC
source setup-environment frdm-imx93
bitbake xoc-bundle
# ... install bundle as above
```

## 4. Service Management

### Check service status:

```bash
ssh root@192.168.68.100 "systemctl status privacy-dashboard"
ssh root@192.168.68.100 "systemctl status device-tracker"
```

### View logs:

```bash
# Dashboard logs
ssh root@192.168.68.100 "journalctl -u privacy-dashboard -n 50"

# Device tracker logs
ssh root@192.168.68.100 "journalctl -u device-tracker -n 50"

# Follow logs in real-time
ssh root@192.168.68.100 "journalctl -u privacy-dashboard -f"
```

### Restart services:

```bash
ssh root@192.168.68.100 "systemctl restart privacy-dashboard device-tracker"
```

## 5. Database Access

### Query device tracker database:

```bash
ssh root@192.168.68.100 "sqlite3 /var/lib/device-tracker/device_tracker.db"
```

Example queries:
```sql
-- List all devices
SELECT * FROM devices;

-- Recent queries
SELECT * FROM dns_queries ORDER BY timestamp DESC LIMIT 20;

-- Top trackers
SELECT domain, COUNT(*) as count FROM dns_queries 
WHERE is_tracker = 1 GROUP BY domain ORDER BY count DESC LIMIT 10;
```

## 6. File Locations on Board

- **Dashboard app**: `/usr/bin/privacy-dashboard`
- **Dashboard templates**: `/usr/share/privacy-dashboard/templates/`
- **Dashboard static**: `/usr/share/privacy-dashboard/static/`
- **Device tracker**: `/usr/bin/device-tracker`
- **Database**: `/var/lib/device-tracker/device_tracker.db`
- **dnsmasq config**: `/etc/dnsmasq.d/01-privacy-box.conf`
- **dnsmasq log**: `/var/log/pihole/pihole.log`
- **RAUC config**: `/etc/rauc/system.conf`

## 7. Troubleshooting

### Dashboard not loading:

```bash
# Check if service is running
ssh root@192.168.68.100 "systemctl status privacy-dashboard"

# Check if port is listening
ssh root@192.168.68.100 "netstat -tlnp | grep 8080"

# Check logs
ssh root@192.168.68.100 "journalctl -u privacy-dashboard -n 100"
```

### Device tracker not working:

```bash
# Check if dnsmasq is logging
ssh root@192.168.68.100 "tail -f /var/log/pihole/pihole.log"

# Check database
ssh root@192.168.68.100 "ls -lh /var/lib/device-tracker/"

# Check device tracker logs
ssh root@192.168.68.100 "journalctl -u device-tracker -n 100"
```

### RAUC update fails:

```bash
# Check RAUC status
ssh root@192.168.68.100 "rauc status --detailed"

# Check partition labels
ssh root@192.168.68.100 "blkid | grep rootfs"

# Check RAUC config
ssh root@192.168.68.100 "cat /etc/rauc/system.conf"
```

