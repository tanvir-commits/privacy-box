SUMMARY = "Create dnsmasq log directory"
DESCRIPTION = "Creates /var/log/pihole directory for dnsmasq logging"
LICENSE = "MIT"
LIC_FILES_CHKSUM = "file://${COMMON_LICENSE_DIR}/MIT;md5=0835ade698e0bcf8506ecda2f7b4f302"

SRC_URI = "file://pihole-log.conf"

S = "${WORKDIR}"

do_install() {
    install -d ${D}${sysconfdir}/tmpfiles.d
    install -m 0644 ${WORKDIR}/pihole-log.conf ${D}${sysconfdir}/tmpfiles.d/pihole-log.conf
}

FILES:${PN} += "${sysconfdir}/tmpfiles.d/pihole-log.conf"

