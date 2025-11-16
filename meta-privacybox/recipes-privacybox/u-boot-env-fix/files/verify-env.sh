#!/bin/sh
# Verify U-Boot environment configuration for RAUC

echo "=== U-Boot Environment Verification ==="

# Check if fw_env.config exists
if [ ! -f /etc/fw_env.config ]; then
    echo "ERROR: /etc/fw_env.config not found!"
    echo "Creating it..."
    mkdir -p /etc
    cat > /etc/fw_env.config << 'EOF'
# Configuration file for fw_(printenv/setenv) utility.
# Block device name	Device offset	Env. size
/dev/mmcblk1		0x1000000		0x4000
EOF
    chmod 644 /etc/fw_env.config
    echo "Created /etc/fw_env.config"
else
    echo "✓ /etc/fw_env.config exists"
    cat /etc/fw_env.config
fi

# Check if fw_printenv works
echo ""
echo "=== Testing fw_printenv ==="
if command -v fw_printenv >/dev/null 2>&1; then
    echo "✓ fw_printenv found"
    echo "Current environment variables:"
    fw_printenv 2>&1 | head -10
else
    echo "✗ fw_printenv not found - u-boot-fw-utils may not be installed"
    exit 1
fi

# Test reading a variable
echo ""
echo "=== Testing environment read ==="
fw_printenv BOOT_ORDER 2>&1
fw_printenv BOOT_A_LEFT 2>&1
fw_printenv BOOT_B_LEFT 2>&1

# Test writing (non-destructive)
echo ""
echo "=== Testing environment write ==="
if command -v fw_setenv >/dev/null 2>&1; then
    echo "✓ fw_setenv found"
    echo "Testing write capability..."
    OLD_VAL=$(fw_printenv TEST_VAR 2>/dev/null | cut -d= -f2)
    fw_setenv TEST_VAR "test_$(date +%s)" 2>&1
    NEW_VAL=$(fw_printenv TEST_VAR 2>/dev/null | cut -d= -f2)
    if [ -n "$NEW_VAL" ]; then
        echo "✓ Write test successful: TEST_VAR=$NEW_VAL"
        # Restore or delete test variable
        if [ -n "$OLD_VAL" ]; then
            fw_setenv TEST_VAR "$OLD_VAL" 2>&1
        else
            fw_setenv TEST_VAR 2>&1  # Delete if it didn't exist
        fi
    else
        echo "✗ Write test failed - check permissions"
    fi
else
    echo "✗ fw_setenv not found"
    exit 1
fi

echo ""
echo "=== Environment verification complete ==="
echo "RAUC should be able to use fw_setenv/fw_printenv now"

exit 0

