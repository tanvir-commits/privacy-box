# Privacy Box Build Instructions

## Quick Start

1. **Source the environment:**
```bash
cd /home/a/yocto/builds/RAUC
source setup-environment frdm-imx93
```

2. **Build the image:**
```bash
bitbake core-image-minimal
```

3. **Or build individual packages first:**
```bash
bitbake device-tracker privacy-dashboard blocklist-updater
```

4. **Flash the image:**
The image will be in: `tmp/deploy/images/imx93frdm/core-image-minimal-imx93frdm.wic`

## Package Structure

All recipes are in: `/home/a/yocto/projects/privacy-box/meta-privacybox/`

- `device-tracker` - Python service for per-device DNS attribution
- `privacy-dashboard` - Flask web interface
- `blocklist-updater` - Downloads and updates tracker blocklists
- `dnsmasq-privacy` - dnsmasq configuration for query logging

## Services

After boot, the following services will be running:
- `device-tracker.service` - Tracks DNS queries per device
- `privacy-dashboard.service` - Web interface on port 8080
- `blocklist-updater.timer` - Updates blocklists daily

## Access

Once booted, access the dashboard at: `http://<board-ip>:8080`


