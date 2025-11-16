#!/bin/bash
# Verification script to run after board reboot
# Usage: ./verify_after_reboot.sh [board_ip]

BOARD_IP="${1:-192.168.68.100}"

echo "=== Privacy Box Post-Reboot Verification ==="
echo "Board IP: $BOARD_IP"
echo ""

# Wait for board to be reachable
echo "1. Waiting for board to be reachable..."
for i in {1..30}; do
    if ping -c 1 -W 1 $BOARD_IP > /dev/null 2>&1; then
        echo "   ✓ Board is reachable"
        break
    fi
    if [ $i -eq 30 ]; then
        echo "   ✗ Board not reachable after 30 seconds"
        exit 1
    fi
    sleep 1
done

# Wait a bit more for services to start
echo ""
echo "2. Waiting for services to start (10 seconds)..."
sleep 10

# Check services
echo ""
echo "3. Checking systemd services..."
ssh root@$BOARD_IP "systemctl is-active device-tracker privacy-dashboard dnsmasq sshd" 2>/dev/null
if [ $? -eq 0 ]; then
    echo "   ✓ All services are active"
else
    echo "   ✗ Some services are not active"
    ssh root@$BOARD_IP "systemctl status device-tracker privacy-dashboard dnsmasq --no-pager -l | tail -20"
fi

# Check if services are enabled
echo ""
echo "4. Checking if services are enabled (survive reboot)..."
ssh root@$BOARD_IP "systemctl is-enabled device-tracker privacy-dashboard dnsmasq sshd" 2>/dev/null | grep -q enabled
if [ $? -eq 0 ]; then
    echo "   ✓ All services are enabled"
else
    echo "   ✗ Some services are not enabled"
fi

# Check OUI database
echo ""
echo "5. Checking OUI database..."
OUI_COUNT=$(ssh root@$BOARD_IP "wc -l /usr/share/device-tracker/oui-database.txt 2>/dev/null | awk '{print \$1}'" 2>/dev/null)
if [ "$OUI_COUNT" = "4267" ]; then
    echo "   ✓ OUI database present (4267 lines = 4262 entries)"
else
    echo "   ✗ OUI database issue (expected 4267, got $OUI_COUNT)"
fi

# Check device identification
echo ""
echo "6. Checking device identification..."
APPLE_COUNT=$(ssh root@$BOARD_IP "python3 << 'PYEOF'
import sqlite3
db = sqlite3.connect('/var/lib/device-tracker/device_tracker.db')
cursor = db.cursor()
cursor.execute('SELECT COUNT(*) FROM devices WHERE name LIKE \"%Apple%\" OR name LIKE \"%iPhone%\" OR name LIKE \"%iPad%\"')
print(cursor.fetchone()[0])
db.close()
PYEOF
" 2>/dev/null)

if [ -n "$APPLE_COUNT" ] && [ "$APPLE_COUNT" -gt 0 ]; then
    echo "   ✓ Apple devices identified: $APPLE_COUNT"
    ssh root@$BOARD_IP "python3 << 'PYEOF'
import sqlite3
db = sqlite3.connect('/var/lib/device-tracker/device_tracker.db')
cursor = db.cursor()
cursor.execute('SELECT ip, name FROM devices WHERE name LIKE \"%Apple%\" OR name LIKE \"%iPhone%\" OR name LIKE \"%iPad%\"')
for ip, name in cursor.fetchall():
    print(f'     {ip} -> {name}')
db.close()
PYEOF
" 2>/dev/null
else
    echo "   ⚠ No Apple devices found yet (may need time to detect)"
fi

# Check dashboard
echo ""
echo "7. Checking dashboard API..."
DASHBOARD_RESPONSE=$(ssh root@$BOARD_IP "curl -s http://localhost:8080/api/network/stats" 2>/dev/null)
if echo "$DASHBOARD_RESPONSE" | grep -q "device_count"; then
    echo "   ✓ Dashboard API responding"
    DEVICE_COUNT=$(echo "$DASHBOARD_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['network']['device_count'])" 2>/dev/null)
    echo "     Devices detected: $DEVICE_COUNT"
else
    echo "   ✗ Dashboard API not responding"
fi

# Check device-tracker logs
echo ""
echo "8. Checking device-tracker logs (last 5 lines)..."
ssh root@$BOARD_IP "journalctl -u device-tracker --no-pager -n 5" 2>/dev/null | tail -5

# Check privacy-dashboard logs
echo ""
echo "9. Checking privacy-dashboard logs (last 5 lines)..."
ssh root@$BOARD_IP "journalctl -u privacy-dashboard --no-pager -n 5" 2>/dev/null | tail -5

echo ""
echo "=== Verification Complete ==="
echo ""
echo "Next steps:"
echo "1. Open dashboard: http://$BOARD_IP:8080"
echo "2. Check device list and search for 'Apple' or 'iPhone'"
echo "3. Test device detail modal by clicking on a device"
echo "4. Verify network-wide top domains section"

