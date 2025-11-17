#!/bin/sh
# Download IP2Location DB3 Lite database
# Free database from: https://lite.ip2location.com/database/ip-country
# Note: This requires a free account. The URL format may have changed.
# For now, this script will attempt download but gracefully fail if URL is incorrect.

DB_PATH="/usr/share/device-tracker/IP2LOCATION-LITE-DB3.BIN"
FALLBACK_PATH="/etc/device-tracker/IP2LOCATION-LITE-DB3.BIN"

# Check if database already exists
if [ -f "$DB_PATH" ]; then
    echo "IP2Location database already exists at $DB_PATH"
    exit 0
fi

if [ -f "$FALLBACK_PATH" ]; then
    echo "IP2Location database already exists at $FALLBACK_PATH"
    exit 0
fi

echo "IP2Location database not found."
echo "Note: Database download requires free account registration."
echo "Please download manually from: https://lite.ip2location.com/database/ip-country"
echo "Then copy to: $DB_PATH or $FALLBACK_PATH"
echo ""
echo "Geolocation will be disabled until database is available."
exit 0  # Don't fail - geolocation is optional

