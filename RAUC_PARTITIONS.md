# RAUC and A/B Partitions Configuration

## ✅ Yes, the image includes RAUC and A/B partitions!

### RAUC (Robust Auto-Update Controller)

**Enabled in image:**
- ✅ `rauc` package installed
- ✅ `rauc-service` installed  
- ✅ RAUC feature enabled in DISTRO_FEATURES
- ✅ U-Boot environment utilities included

**Configuration:**
```bash
DISTRO_FEATURES:append = " rauc systemd usrmerge"
CORE_IMAGE_EXTRA_INSTALL += " rauc rauc-service u-boot-fw-utils u-boot-env-config"
```

### A/B Partition Layout

The image uses `xoc-dualboot.wks` which creates:

1. **U-Boot** (raw copy at sector 32)
   - Bootloader partition

2. **/boot** (FAT32, 128MB, starts at 32MB)
   - Kernel and device tree files
   - Boot partition

3. **rootfsA** (ext4, 1536MB)
   - Primary root filesystem slot
   - Currently active

4. **rootfsB** (ext4, 1536MB)  
   - Secondary root filesystem slot
   - Used for OTA updates

5. **/config** (ext4, 64MB)
   - Persistent configuration partition
   - Survives OTA updates

6. **/data** (ext4, 512MB)
   - Data partition

### Partition Table
- **Type**: MBR (not GPT)
- **Reason**: Avoids conflict with bootloader at sector 32
- **Layout**: Bootloader at sector 32, partitions start at 32MB

### RAUC Update Process

1. **Update bundle** is installed to inactive slot (rootfsA or rootfsB)
2. **RAUC verifies** the bundle signature
3. **System reboots** and switches to updated slot
4. **Rollback** available if update fails

### Privacy Box + RAUC

The privacy box components are installed in both rootfs slots:
- device-tracker
- privacy-dashboard  
- blocklist-updater
- dnsmasq configuration

All will be updated together when you deploy a new RAUC bundle.

## Verification

To verify RAUC is working after boot:
```bash
rauc status
rauc info
```

To check partitions:
```bash
lsblk
mount | grep rootfs
```


