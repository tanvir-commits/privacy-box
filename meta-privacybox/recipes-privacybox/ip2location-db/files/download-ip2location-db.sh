#!/bin/sh
# Download IP2Location DB3 Lite database
# Free database from: https://lite.ip2location.com/database/ip-country

DB_URL="https://download.ip2location.com/lite/IP2LOCATION-LITE-DB3.BIN"
DB_PATH="/usr/share/device-tracker/IP2LOCATION-LITE-DB3.BIN"
FALLBACK_PATH="/etc/device-tracker/IP2LOCATION-LITE-DB3.BIN"

echo "Downloading IP2Location DB3 Lite database..."

# Try primary location first
mkdir -p "$(dirname "$DB_PATH")"
if wget -O "$DB_PATH" "$DB_URL" 2>/dev/null || curl -o "$DB_PATH" "$DB_URL" 2>/dev/null; then
    echo "Database downloaded to $DB_PATH"
    exit 0
fi

# Fallback location
mkdir -p "$(dirname "$FALLBACK_PATH")"
if wget -O "$FALLBACK_PATH" "$DB_URL" 2>/dev/null || curl -o "$FALLBACK_PATH" "$DB_URL" 2>/dev/null; then
    echo "Database downloaded to $FALLBACK_PATH"
    exit 0
fi

echo "Error: Failed to download IP2Location database"
echo "Please download manually from: https://lite.ip2location.com/database/ip-country"
exit 1

