#!/bin/sh
# Pi-hole setup script for plug-and-play configuration

PIHOLE_DIR="/etc/pihole"
GRAVITY_DB="${PIHOLE_DIR}/gravity.db"

# Initialize Pi-hole if not already done
if [ ! -f "${GRAVITY_DB}" ]; then
    # Create gravity database
    sqlite3 "${GRAVITY_DB}" <<EOF
CREATE TABLE IF NOT EXISTS gravity (domain TEXT PRIMARY KEY);
CREATE TABLE IF NOT EXISTS adlist (id INTEGER PRIMARY KEY, address TEXT);
EOF
fi

# Configure dnsmasq for per-device logging
cat > /etc/dnsmasq.d/01-pihole.conf <<EOF
# Pi-hole configuration
log-queries
log-facility=/var/log/pihole/pihole.log
addn-hosts=/etc/pihole/gravity.list
EOF

# Download blocklists on first run
if [ ! -f "${PIHOLE_DIR}/gravity.list" ]; then
    /usr/bin/pihole-update-blocklists
fi


