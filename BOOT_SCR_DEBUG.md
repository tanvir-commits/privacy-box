# Boot.scr Debugging

## Issue
U-Boot reports "Unknown image format!" when checking boot.scr with `iminfo`, even though:
- ✅ File has correct U-Boot magic number (27 05 19 56)
- ✅ File command shows: "u-boot legacy uImage, Linux/ARM 64-bit, Script File"
- ✅ File is correctly generated from boot.cmd

## Analysis

The boot.scr file is correctly formatted. The issue might be:

1. **U-Boot version mismatch**: The board's U-Boot might not support legacy uImage format for scripts
2. **iminfo limitation**: `iminfo` might not recognize script images, but `source` command might still work
3. **Format change needed**: Might need to use a different format (FIT script instead of legacy)

## Test in U-Boot

Even if `iminfo` fails, try:
```
fatload mmc 1:1 $loadaddr boot.scr
source $loadaddr
```

If `source` works, then the issue is just with `iminfo` not recognizing the format, but the script will execute.

## Possible Solutions

1. **Test if source works despite iminfo failure** - The script might execute even if iminfo doesn't recognize it
2. **Check U-Boot version** - Verify if board U-Boot supports legacy script format
3. **Use FIT script format** - Convert to FIT format if legacy isn't supported
4. **Check bootscript command** - The issue might be in how U-Boot's bootscript command loads it

## Next Steps

1. Try `source $loadaddr` directly in U-Boot (after loading boot.scr)
2. Check U-Boot version and capabilities
3. If source works, the issue is just iminfo, not the actual boot process


