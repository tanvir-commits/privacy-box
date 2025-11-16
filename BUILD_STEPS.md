# Build Steps - Privacy Box

## Step 1: Source the Build Environment

You need to source the Yocto build environment first. Since the build directory `frdm-imx93` already exists, use:

```bash
cd /home/a/yocto/builds/RAUC
source sources/base/setup-environment frdm-imx93
```

This will:
- Set up all the necessary environment variables
- Add bitbake to your PATH
- Configure the build directory

**Important**: You must run this in your shell (not in a script) because it modifies your shell environment.

## Step 2: Verify Environment

After sourcing, verify bitbake is available:

```bash
which bitbake
```

You should see the path to bitbake.

## Step 3: Build Individual Packages (Optional - for testing)

Build the privacy box packages individually first:

```bash
bitbake device-tracker
bitbake privacy-dashboard
bitbake blocklist-updater
```

## Step 4: Build Complete Image

Build the full image with all privacy box components:

```bash
bitbake core-image-minimal
```

## Step 5: Find the Image

After building, the image will be in:

```bash
tmp/deploy/images/imx93frdm/core-image-minimal-imx93frdm.wic
```

## Troubleshooting

If you get "bitbake: command not found":
- Make sure you sourced the environment: `source sources/base/setup-environment frdm-imx93`
- You must run this in an interactive shell, not in a script

If you get parsing errors:
- All recipes have been validated and should parse correctly
- Check that the meta-privacybox layer is in bblayers.conf

## Quick Start (All in One)

```bash
cd /home/a/yocto/builds/RAUC
source sources/base/setup-environment frdm-imx93
bitbake core-image-minimal
```


