#!/bin/sh
# Initialize U-Boot environment if it doesn't exist
# NOTE: Environment must be initialized from U-Boot console first:
#   In U-Boot: env default -a
#   In U-Boot: saveenv
# This script just verifies it's working

echo "=== U-Boot Environment Verification ==="

# Check if fw_env.config exists
if [ ! -f /etc/fw_env.config ]; then
    echo "ERROR: /etc/fw_env.config not found!"
    exit 1
fi

# Check if device exists
if [ ! -b /dev/mmcblk1 ]; then
    echo "ERROR: /dev/mmcblk1 does not exist!"
    exit 1
fi

# Try to read environment
if fw_printenv BOOT_ORDER >/dev/null 2>&1; then
    echo "✓ Environment is readable"
    echo "Current BOOT_ORDER:"
    fw_printenv BOOT_ORDER
    exit 0
fi

echo "✗ Environment is not readable"
echo ""
echo "The environment needs to be initialized from U-Boot console."
echo ""
echo "To initialize:"
echo "1. Interrupt U-Boot boot (press any key during boot)"
echo "2. In U-Boot console, run:"
echo "   => env default -a"
echo "   => saveenv"
echo "3. Reboot and environment will be initialized"
echo ""
echo "This only needs to be done once. After initialization,"
echo "RAUC will be able to read and write environment variables."
echo ""
echo "Environment location: /dev/mmcblk1 at offset 0x1000000 (16MB)"
echo "This is safe - it's before the boot partition starts at 64MB"

exit 1
