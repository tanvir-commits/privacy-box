#!/bin/bash
# RAUC OTA Update Test Script
# Run this on the board via SSH to test OTA update from http://192.168.68.100/

set -e

UPDATE_SERVER="http://192.168.68.100"
BOARD_IP="192.168.68.100"

echo "=== RAUC OTA Update Test ==="
echo ""

# 1) Check current RAUC status
echo "1. Current RAUC status:"
rauc status || echo "  Warning: rauc status failed"
echo ""

# 2) Check U-Boot environment
echo "2. U-Boot environment:"
if fw_printenv rauc.slot 2>/dev/null; then
    echo "  ✓ rauc.slot is set"
else
    echo "  ✗ rauc.slot not set - RAUC may not find primary slot"
fi
fw_printenv BOOT_ORDER 2>/dev/null || echo "  BOOT_ORDER not set"
echo ""

# 3) Test server connectivity
echo "3. Testing update server ($UPDATE_SERVER)..."
if curl -I "$UPDATE_SERVER/" 2>&1 | head -1 | grep -q "HTTP"; then
    echo "  ✓ Server is accessible"
    
    # 4) List available bundles
    echo ""
    echo "4. Available bundles:"
    BUNDLES=$(curl -s "$UPDATE_SERVER/" 2>/dev/null | grep -oE 'href="[^"]*\.raucb[^"]*"' | sed 's/href="//;s/"//' | head -5)
    
    if [ -z "$BUNDLES" ]; then
        # Try alternative parsing
        BUNDLES=$(curl -s "$UPDATE_SERVER/" 2>/dev/null | grep -i "\.raucb" | grep -oE '[^<>"]+\.raucb[^<>"]*' | head -5)
    fi
    
    if [ -n "$BUNDLES" ]; then
        echo "$BUNDLES" | while read bundle; do
            echo "  - $bundle"
        done
        
        # 5) Ask user which bundle to install
        echo ""
        FIRST_BUNDLE=$(echo "$BUNDLES" | head -1)
        echo "5. Found bundle: $FIRST_BUNDLE"
        echo ""
        read -p "Install this bundle? (yes/no): " confirm
        
        if [ "$confirm" = "yes" ]; then
            echo ""
            echo "Installing update: $FIRST_BUNDLE"
            echo "URL: $UPDATE_SERVER/$FIRST_BUNDLE"
            echo ""
            rauc install "$UPDATE_SERVER/$FIRST_BUNDLE"
            
            # 6) Check status after install
            echo ""
            echo "6. Status after install:"
            rauc status -v
            
            echo ""
            echo "✓ Update installed successfully!"
            echo "  Reboot to test the update, then run: rauc status mark-good"
        else
            echo "Update cancelled"
        fi
    else
        echo "  No .raucb files found in directory listing"
        echo ""
        echo "  To manually install, run:"
        echo "    rauc install $UPDATE_SERVER/<bundle-name>.raucb"
        echo ""
        echo "  Or list files manually:"
        curl -s "$UPDATE_SERVER/" | head -20
    fi
else
    echo "  ✗ Server not accessible"
    echo "  Make sure update server is running at $UPDATE_SERVER/"
    echo ""
    echo "  To set up a test server on build machine:"
    echo "    cd /home/a/yocto/builds/RAUC/frdm-imx93/tmp/deploy/images/imx93frdm"
    echo "    python3 -m http.server 8000"
fi

