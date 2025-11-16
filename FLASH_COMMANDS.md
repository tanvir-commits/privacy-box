# Flash Commands - Direct

## Simple Command (with full path)

```bash
# Unmount
sudo umount /dev/sda* 2>/dev/null

# Flash (use full path)
sudo dd if=/home/a/yocto/builds/RAUC/frdm-imx93/tmp/deploy/images/imx93frdm/core-image-minimal-imx93frdm.rootfs-20251115175625.wic of=/dev/sda bs=1M status=progress conv=fsync
```

## Or use the script

```bash
/home/a/yocto/projects/privacy-box/flash_image.sh
```

## Debug: Check what happened

If the command seemed to do nothing, check:

```bash
# Check if image exists
ls -lh /home/a/yocto/builds/RAUC/frdm-imx93/tmp/deploy/images/imx93frdm/core-image-minimal-imx93frdm.rootfs-*.wic

# Check device
ls -l /dev/sda

# Check if mounted
mount | grep sda

# Try with explicit error checking
sudo dd if=/home/a/yocto/builds/RAUC/frdm-imx93/tmp/deploy/images/imx93frdm/core-image-minimal-imx93frdm.rootfs-20251115175625.wic of=/dev/sda bs=1M status=progress conv=fsync 2>&1
```

## Alternative: Use bmaptool (faster)

```bash
sudo umount /dev/sda* 2>/dev/null
sudo bmaptool copy /home/a/yocto/builds/RAUC/frdm-imx93/tmp/deploy/images/imx93frdm/core-image-minimal-imx93frdm.rootfs-20251115175625.wic /dev/sda
```


