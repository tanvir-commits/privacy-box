SUMMARY = "MAC Address Setter - Sets permanent MAC address for network interfaces"
DESCRIPTION = "Service that sets a fixed MAC address for eth0 and eth1 at boot"
LICENSE = "MIT"
LIC_FILES_CHKSUM = "file://${COMMON_LICENSE_DIR}/MIT;md5=0835ade698e0bcf8506ecda2f7b4f302"

SRC_URI = " \
    file://set-mac-address.sh \
    file://set-mac-address.service \
"

S = "${WORKDIR}"

inherit systemd

RDEPENDS:${PN} = "iproute2"

SYSTEMD_SERVICE:${PN} = "set-mac-address.service"

do_install() {
    install -d ${D}${bindir}
    install -d ${D}${systemd_system_unitdir}

    # Install script
    install -m 0755 ${WORKDIR}/set-mac-address.sh ${D}${bindir}/set-mac-address

    # Install systemd service
    install -m 0644 ${WORKDIR}/set-mac-address.service ${D}${systemd_system_unitdir}/
}

FILES:${PN} += " \
    ${bindir}/set-mac-address \
    ${systemd_system_unitdir}/set-mac-address.service \
"

