# Flash Image to SD Card

## Prerequisites
- SD card is always `/dev/sda`
- Image location: `/home/a/yocto/builds/RAUC/frdm-imx93/tmp/deploy/images/imx93frdm/core-image-minimal-imx93frdm.rootfs-*.wic`

## Step 1: Unmount all partitions on /dev/sda

```bash
# Unmount all mounted partitions
sudo umount /dev/sda* 2>/dev/null

# Verify nothing is mounted
mount | grep sda
```

## Step 2: Flash the image

```bash
# Find the latest WIC image
IMAGE=$(ls -t /home/a/yocto/builds/RAUC/frdm-imx93/tmp/deploy/images/imx93frdm/core-image-minimal-imx93frdm.rootfs-*.wic | head -1)

# Flash to SD card
sudo dd if="$IMAGE" of=/dev/sda bs=1M status=progress conv=fsync
```

## One-liner (all in one)

```bash
sudo umount /dev/sda* 2>/dev/null && \
IMAGE=$(ls -t /home/a/yocto/builds/RAUC/frdm-imx93/tmp/deploy/images/imx93frdm/core-image-minimal-imx93frdm.rootfs-*.wic | head -1) && \
sudo dd if="$IMAGE" of=/dev/sda bs=1M status=progress conv=fsync
```

## Verification (optional)

After flashing, verify the partitions:

```bash
sudo fdisk -l /dev/sda
```

You should see:
- Partition 1: Boot (FAT32)
- Partition 2: rootfsA (1.9GB)
- Partition 3: rootfsB (1.9GB)
- Partition 5: /config (64MB)
- Partition 6: /data (512MB)

## Safety Notes

⚠️ **WARNING**: This will erase everything on `/dev/sda`!

- Make sure `/dev/sda` is your SD card, not your system disk
- Double-check with `lsblk` before running
- The `conv=fsync` ensures data is written before command completes


