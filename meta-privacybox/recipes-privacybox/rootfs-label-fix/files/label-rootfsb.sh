#!/bin/sh
# Label rootfsB partition if it exists and is not already labeled

ROOTFSB_DEV="/dev/mmcblk1p3"
ROOTFSB_LABEL="rootfsB"

# Check if device exists
if [ ! -b "$ROOTFSB_DEV" ]; then
    echo "rootfsB device $ROOTFSB_DEV not found"
    exit 0
fi

# Check current label
CURRENT_LABEL=$(blkid -s LABEL -o value "$ROOTFSB_DEV" 2>/dev/null)

if [ "$CURRENT_LABEL" = "$ROOTFSB_LABEL" ]; then
    echo "rootfsB partition already labeled correctly"
    exit 0
fi

# Check if partition is formatted (has a filesystem)
FS_TYPE=$(blkid -s TYPE -o value "$ROOTFSB_DEV" 2>/dev/null)

if [ -z "$FS_TYPE" ]; then
    echo "rootfsB partition not formatted, skipping label"
    exit 0
fi

# Set the label
echo "Labeling $ROOTFSB_DEV as $ROOTFSB_LABEL..."
if tune2fs -L "$ROOTFSB_LABEL" "$ROOTFSB_DEV" 2>/dev/null; then
    echo "✓ Successfully labeled rootfsB partition"
    # Update udev to recognize the new label
    udevadm trigger --subsystem-match=block --action=change
else
    echo "✗ Failed to label rootfsB partition"
    exit 1
fi

