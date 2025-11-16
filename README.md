# Privacy Box - Per-Device DNS Tracking

**World's First Plug-and-Play Privacy Box That Shows You What Each Device Is Actually Doing**

A privacy-focused network device that provides per-device DNS query tracking, visualization, and blocking capabilities. Built for the i.MX93 FRDM board using Yocto Linux.

## Features

- 🔍 **Per-Device Tracking**: See exactly which device on your network is making which DNS queries
- 📊 **Real-Time Dashboard**: Beautiful web interface showing device activity, tracker queries, and statistics
- 🛡️ **Tracker Detection**: Automatically identifies and can block known tracking domains
- 🔌 **Plug-and-Play**: Acts as DHCP server and DNS forwarder - just connect to your network
- 📱 **Mobile Responsive**: Dashboard works on desktop and mobile devices

## Hardware

- **Board**: NXP i.MX93 11x11 FRDM
- **CPU**: ARM Cortex-A55 @ 1.7GHz
- **Network**: Dual Gigabit Ethernet (eth0, eth1)
- **Storage**: SD Card (RAUC A/B partitions)

## Software Stack

- **OS**: Yocto Linux (Poky Scarthgap)
- **Init**: systemd
- **DNS/DHCP**: dnsmasq
- **Tracking**: Python 3 + SQLite3
- **Dashboard**: Flask + Flask-CORS
- **Update System**: RAUC (A/B partitioning)

## Project Structure

```
meta-privacybox/
├── conf/
│   └── layer.conf              # Yocto layer configuration
├── recipes-privacybox/
│   ├── device-tracker/         # DNS query attribution service
│   ├── privacy-dashboard/      # Web dashboard (Flask)
│   ├── blocklist-updater/      # Tracker blocklist management
│   ├── mac-address-setter/     # Permanent MAC address service
│   └── dnsmasq-logdir/         # Log directory creation
└── recipes-support/
    └── dnsmasq/                # dnsmasq configuration
```

## Building

### Prerequisites

- Yocto build environment set up
- Access to meta-xoc-rauc and meta-rauc-nxp layers
- i.MX93 BSP layers

### Build Steps

1. Source the build environment:
```bash
cd /home/a/yocto/builds/RAUC
source setup-environment frdm-imx93
```

2. The `meta-privacybox` layer should already be in `bblayers.conf`. If not, add:
```bash
BBLAYERS += " \
    /home/a/yocto/projects/privacy-box/meta-privacybox \
"
```

3. Build the image:
```bash
bitbake core-image-minimal
```

4. Flash to SD card:
```bash
cd /home/a/yocto/projects/privacy-box
./flash_image.sh
```

## Components

### device-tracker
Python service that:
- Reads dnsmasq query logs from `/var/log/pihole/pihole.log`
- Correlates DNS queries with DHCP leases to identify devices
- Stores per-device query data in SQLite database
- Identifies tracker domains using keyword matching
- Provides REST API for dashboard

### privacy-dashboard
Flask web application providing:
- Real-time per-device DNS query visualization
- Network-wide statistics (total queries, trackers, blocked)
- Device-specific tracking details
- Beautiful, modern UI with mobile support
- RESTful API endpoints

### dnsmasq Configuration
Custom dnsmasq setup:
- Query logging to `/var/log/pihole/pihole.log`
- DHCP server for device identification
- Blocklist support via `/etc/privacy-box/blocklist.txt`
- DNS forwarding to upstream servers

### mac-address-setter
Systemd service that:
- Sets permanent MAC addresses for eth0 and eth1 at boot
- Ensures consistent IP addresses from DHCP
- Configurable MAC addresses in script

## Usage

### Initial Setup

1. Flash the image to SD card (see Building section)
2. Insert SD card into i.MX93 FRDM board
3. Connect board to your network via Ethernet
4. Power on the board

### Network Configuration

The board will:
- Set MAC addresses: eth0=`02:00:00:00:00:10`, eth1=`02:00:00:00:00:20`
- Start dnsmasq as DHCP server (range: 192.168.68.100-200)
- Start DNS forwarding service
- Create log directory at `/var/log/pihole/`

### Accessing the Dashboard

1. Find the board's IP address (check your router's DHCP client list)
2. Open browser to: `http://<board-ip>:8080`
3. View real-time device tracking and DNS queries

### API Endpoints

- `GET /api/devices` - List all devices with query counts
- `GET /api/activity` - Get recent DNS query activity
- `GET /api/stats` - Get network statistics

## Configuration

### MAC Addresses

Edit `/usr/bin/set-mac-address` on the board, or modify:
`meta-privacybox/recipes-privacybox/mac-address-setter/files/set-mac-address.sh`

### DHCP Range

Edit `/etc/dnsmasq.d/01-privacy-box.conf`:
```
dhcp-range=192.168.68.100,192.168.68.200,12h
```

### DNS Server IP

Update the DNS server IP in dnsmasq config:
```
dhcp-option=option:dns-server,192.168.68.116
```

## Development

### Adding New Recipes

1. Create recipe directory: `meta-privacybox/recipes-privacybox/<package-name>/`
2. Add recipe file: `<package-name>_<version>.bb`
3. Add source files in `files/` subdirectory
4. Rebuild: `bitbake <package-name>`

### Testing Changes

1. Build package: `bitbake <package-name>`
2. Rebuild image: `bitbake core-image-minimal`
3. Flash to SD card: `./flash_image.sh`
4. Test on board

## Troubleshooting

### dnsmasq not starting
- Check log directory exists: `ls -la /var/log/pihole/`
- Check config: `dnsmasq --test`
- View logs: `journalctl -u dnsmasq.service`

### device-tracker not processing
- Check dnsmasq is logging: `tail -f /var/log/pihole/pihole.log`
- Check service status: `systemctl status device-tracker.service`
- View logs: `journalctl -u device-tracker.service`

### Dashboard not accessible
- Check service: `systemctl status privacy-dashboard.service`
- Check port: `netstat -tlnp | grep 8080`
- Check firewall/network connectivity

## License

MIT License - See individual component licenses

## Contributing

This is a private project. For questions or issues, contact the maintainer.
