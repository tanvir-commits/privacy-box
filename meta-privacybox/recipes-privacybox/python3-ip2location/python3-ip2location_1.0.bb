SUMMARY = "IP2Location Python Library"
DESCRIPTION = "Python library for IP2Location database lookups"
LICENSE = "MIT"
LIC_FILES_CHKSUM = "file://${COMMON_LICENSE_DIR}/MIT;md5=0835ade698e0bcf8506ecda2f7b4f302"

# Install IP2Location via pip at runtime
# We'll use a systemd service or post-install script to install it
# This avoids build-time complexity

SRC_URI = " \
    file://install-ip2location.sh \
    file://ip2location-install.service \
"

S = "${WORKDIR}"

inherit allarch systemd

SYSTEMD_SERVICE:${PN} = "ip2location-install.service"

do_install() {
    install -d ${D}${bindir}
    install -d ${D}${systemd_system_unitdir}
    
    install -m 0755 ${WORKDIR}/install-ip2location.sh ${D}${bindir}/install-ip2location
    install -m 0644 ${WORKDIR}/ip2location-install.service ${D}${systemd_system_unitdir}/
}

FILES:${PN} += " \
    ${bindir}/install-ip2location \
    ${systemd_system_unitdir}/ip2location-install.service \
"

RDEPENDS:${PN} = "python3-pip"

