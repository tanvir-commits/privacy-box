#!/bin/bash
# Update Privacy Box files via SSH
# Usage: ./update_via_ssh.sh [file] [board_ip]

BOARD_IP="${2:-192.168.68.100}"
FILE="${1}"

if [ -z "$FILE" ]; then
    echo "Usage: $0 <file> [board_ip]"
    echo ""
    echo "Examples:"
    echo "  $0 app.py                    # Update dashboard app"
    echo "  $0 templates/index.html      # Update dashboard HTML"
    echo "  $0 device-tracker.py         # Update device tracker"
    echo ""
    echo "File paths (relative to meta-privacybox/recipes-privacybox/):"
    echo "  privacy-dashboard/files/app.py"
    echo "  privacy-dashboard/files/templates/index.html"
    echo "  privacy-dashboard/files/static/style.css"
    echo "  device-tracker/files/device-tracker.py"
    exit 1
fi

# Resolve file path
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FULL_PATH="$SCRIPT_DIR/meta-privacybox/recipes-privacybox/$FILE"

if [ ! -f "$FULL_PATH" ]; then
    echo "ERROR: File not found: $FULL_PATH"
    exit 1
fi

# Determine destination on board
case "$FILE" in
    privacy-dashboard/files/app.py)
        DEST="/usr/bin/privacy-dashboard"
        SERVICE="privacy-dashboard"
        ;;
    privacy-dashboard/files/templates/index.html)
        DEST="/usr/share/privacy-dashboard/templates/index.html"
        SERVICE="privacy-dashboard"
        ;;
    privacy-dashboard/files/static/style.css)
        DEST="/usr/share/privacy-dashboard/static/style.css"
        SERVICE="privacy-dashboard"
        ;;
    device-tracker/files/device-tracker.py)
        DEST="/usr/bin/device-tracker"
        SERVICE="device-tracker"
        ;;
    *)
        echo "ERROR: Unknown file type. Please specify full path."
        echo "Example: privacy-dashboard/files/app.py"
        exit 1
        ;;
esac

echo "=== Privacy Box File Update ==="
echo "File: $FILE"
echo "Source: $FULL_PATH"
echo "Destination: $DEST"
echo "Board: $BOARD_IP"
echo ""

# Copy file
echo "Copying file..."
scp "$FULL_PATH" "root@${BOARD_IP}:${DEST}"

if [ $? -ne 0 ]; then
    echo "ERROR: Failed to copy file"
    exit 1
fi

# Restart service
if [ -n "$SERVICE" ]; then
    echo ""
    echo "Restarting $SERVICE service..."
    ssh "root@${BOARD_IP}" "systemctl restart $SERVICE && systemctl status $SERVICE --no-pager -l"
fi

echo ""
echo "✓ Update complete!"

