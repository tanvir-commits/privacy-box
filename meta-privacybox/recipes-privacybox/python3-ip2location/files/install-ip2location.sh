#!/bin/sh
# Install IP2Location Python library via pip
# This script can be run at boot or manually

if ! python3 -c "import IP2Location" 2>/dev/null; then
    echo "Installing IP2Location Python library..."
    pip3 install --no-index --find-links /tmp IP2Location || \
    pip3 install IP2Location || \
    echo "Warning: Failed to install IP2Location. Geolocation will be disabled."
else
    echo "IP2Location already installed."
fi

