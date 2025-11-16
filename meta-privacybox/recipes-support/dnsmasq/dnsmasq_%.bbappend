# Append to dnsmasq (meta-networking/recipes-support/dnsmasq/dnsmasq_*.bb)
# to add Privacy Box logging and DHCP configuration.

FILESEXTRAPATHS:prepend := "${THISDIR}/files:"

SRC_URI += "file://privacy-box.conf"

do_install:append() {
    # Create dnsmasq configuration for Privacy Box
    install -d ${D}${sysconfdir}/dnsmasq.d
    install -m 0644 ${WORKDIR}/privacy-box.conf \
        ${D}${sysconfdir}/dnsmasq.d/01-privacy-box.conf

    # Log directory will be created at runtime by device-tracker or systemd
}

FILES:${PN} += " \
    ${sysconfdir}/dnsmasq.d/01-privacy-box.conf \
"

