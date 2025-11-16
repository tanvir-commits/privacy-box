# Fixed: dnsmasq.bbappend Location

## Issue
The dnsmasq.bbappend file was in the wrong location, causing bitbake to not find the base recipe.

## Fix Applied
- Removed duplicate: `recipes-privacybox/dnsmasq-privacy/dnsmasq-privacy.bbappend`
- Correct location: `recipes-privacybox/recipes-support/dnsmasq/dnsmasq.bbappend`

The .bbappend file must be in the same directory structure as the base recipe:
- Base recipe: `meta-networking/recipes-support/dnsmasq/dnsmasq_2.90.bb`
- Our append: `meta-privacybox/recipes-privacybox/recipes-support/dnsmasq/dnsmasq.bbappend`

## Test
Now try building again:

```bash
cd /home/a/yocto/builds/RAUC/frdm-imx93
bitbake -p device-tracker privacy-dashboard blocklist-updater
```

The error should be gone now.


