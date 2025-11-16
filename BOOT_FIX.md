# Boot Fix - Added boot.scr

## Problem
U-Boot was failing with:
- "Failed to load 'boot.scr'"
- "Bad Linux ARM64 Image magic!"

## Root Cause
The `boot.scr` file was not included in `IMAGE_BOOT_FILES`, so it wasn't copied to the boot partition.

## Fix Applied
Updated `local.conf` to include `boot.scr`:
```bash
IMAGE_BOOT_FILES = "boot.scr fitImage;Image imx93-11x11-frdm.dtb"
```

## New Image Built
The image has been rebuilt with `boot.scr` included. New image:
- `core-image-minimal-imx93frdm.rootfs-*.wic` (latest timestamp)

## Flash Again

```bash
# Unmount
sudo umount /dev/sda* 2>/dev/null

# Flash new image
IMAGE=$(ls -t /home/a/yocto/builds/RAUC/frdm-imx93/tmp/deploy/images/imx93frdm/core-image-minimal-imx93frdm.rootfs-*.wic | head -1)
sudo dd if="$IMAGE" of=/dev/sda bs=1M status=progress conv=fsync
```

## What boot.scr Does
The boot script:
1. Loads the fitImage kernel
2. Selects the correct rootfs slot (A or B) based on RAUC state
3. Sets up boot arguments
4. Boots the kernel

This is required for RAUC A/B boot functionality.


