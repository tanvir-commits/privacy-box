# Boot Script Issue - "Wrong image format"

## Problem
U-Boot finds and loads `boot.scr` but fails with:
- "Wrong image format for 'source' command"

## Analysis
- ✅ boot.scr file exists and is correctly formatted (u-boot legacy uImage, Script File)
- ✅ File is found and loaded (2708 bytes read)
- ❌ U-Boot fails to execute it with "source" command

## Possible Causes

1. **Address issue**: The script might be loaded to wrong address
2. **Variable issue**: boot.cmd uses `${image}` and `${fdt_file}` which might not be set
3. **U-Boot version**: The bootscript command might have a bug

## Current Status

The image has been rebuilt with:
- ✅ boot.scr included in IMAGE_BOOT_FILES
- ✅ boot.scr regenerated from boot.cmd
- ✅ Image rebuilt successfully

## Next Steps

1. **Flash the new image** and test again
2. If still fails, we may need to:
   - Check U-Boot environment variables
   - Simplify the boot script
   - Use extlinux.conf instead of boot.scr

## Flash Command

```bash
sudo umount /dev/sda* 2>/dev/null
IMAGE=$(ls -t /home/a/yocto/builds/RAUC/frdm-imx93/tmp/deploy/images/imx93frdm/core-image-minimal-imx93frdm.rootfs-*.wic | head -1)
sudo dd if="$IMAGE" of=/dev/sda bs=1M status=progress conv=fsync
```

## U-Boot Debug Commands

If it still fails, try in U-Boot:
```
printenv
printenv loadaddr
printenv script
fatload mmc 1:1 $loadaddr boot.scr
iminfo $loadaddr
source $loadaddr
```


