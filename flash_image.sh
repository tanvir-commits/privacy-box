#!/bin/bash
# Flash Privacy Box image to SD card

set -e

# Image location
IMAGE_DIR="/home/a/yocto/builds/RAUC/frdm-imx93/tmp/deploy/images/imx93frdm"
DEVICE="/dev/sda"

echo "=== Privacy Box Image Flasher ==="
echo ""

# Check if device exists
if [ ! -b "$DEVICE" ]; then
    echo "ERROR: $DEVICE does not exist or is not a block device"
    exit 1
fi

# Find latest image
IMAGE=$(ls -t "$IMAGE_DIR"/core-image-minimal-imx93frdm.rootfs-*.wic 2>/dev/null | head -1)

if [ -z "$IMAGE" ]; then
    echo "ERROR: No WIC image found in $IMAGE_DIR"
    exit 1
fi

echo "Image: $IMAGE"
echo "Size: $(ls -lh "$IMAGE" | awk '{print $5}')"
echo "Device: $DEVICE"
echo ""

# Safety check
read -p "WARNING: This will ERASE everything on $DEVICE. Continue? (yes/no): " confirm
if [ "$confirm" != "yes" ]; then
    echo "Aborted."
    exit 1
fi

# Unmount all partitions
echo "Unmounting partitions..."
sudo umount ${DEVICE}* 2>/dev/null || true
sleep 1

# Verify unmounted
if mount | grep -q "$DEVICE"; then
    echo "WARNING: Some partitions are still mounted:"
    mount | grep "$DEVICE"
    read -p "Force unmount? (yes/no): " force
    if [ "$force" = "yes" ]; then
        sudo umount -l ${DEVICE}* 2>/dev/null || true
    else
        echo "Aborted."
        exit 1
    fi
fi

# Flash the image
echo ""
echo "Flashing image to $DEVICE..."
echo "This may take several minutes..."
echo ""

sudo dd if="$IMAGE" of="$DEVICE" bs=1M status=progress conv=fsync

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Flash completed successfully!"
    echo ""
    echo "Verifying partitions..."
    sudo fdisk -l "$DEVICE" | grep -E "Device|sda[0-9]"
else
    echo ""
    echo "❌ Flash failed!"
    exit 1
fi


