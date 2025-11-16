#!/bin/sh
# Set permanent MAC addresses for network interfaces
# This ensures the device gets the same IP address from DHCP

# MAC addresses for eth0 and eth1
# Format: XX:XX:XX:XX:XX:XX
# Change these to your desired MAC addresses
ETH0_MAC="02:00:00:00:00:10"
ETH1_MAC="02:00:00:00:00:20"

# Set MAC for eth0 if it exists
if [ -e /sys/class/net/eth0 ]; then
    # Only set if current MAC is different (avoid unnecessary changes)
    CURRENT_MAC=$(cat /sys/class/net/eth0/address)
    if [ "$CURRENT_MAC" != "$ETH0_MAC" ]; then
        echo "Setting eth0 MAC to $ETH0_MAC"
        ip link set dev eth0 down
        ip link set dev eth0 address "$ETH0_MAC"
        ip link set dev eth0 up
    fi
fi

# Set MAC for eth1 if it exists
if [ -e /sys/class/net/eth1 ]; then
    CURRENT_MAC=$(cat /sys/class/net/eth1/address)
    if [ "$CURRENT_MAC" != "$ETH1_MAC" ]; then
        echo "Setting eth1 MAC to $ETH1_MAC"
        ip link set dev eth1 down
        ip link set dev eth1 address "$ETH1_MAC"
        ip link set dev eth1 up
    fi
fi

exit 0

