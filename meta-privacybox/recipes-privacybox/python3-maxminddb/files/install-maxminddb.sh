#!/bin/sh
# Install maxminddb Python library via pip
# This script runs at boot to ensure the library is available

if ! python3 -c "import maxminddb" 2>/dev/null; then
    echo "Installing maxminddb Python library..."
    pip3 install maxminddb || \
    echo "Warning: Failed to install maxminddb. Geolocation will be disabled."
else
    echo "maxminddb already installed."
fi

