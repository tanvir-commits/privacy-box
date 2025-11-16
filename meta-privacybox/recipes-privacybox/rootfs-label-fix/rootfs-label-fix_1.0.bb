SUMMARY = "Fix rootfsB Partition Label"
DESCRIPTION = "Service to ensure rootfsB partition is properly labeled on boot"
LICENSE = "MIT"
LIC_FILES_CHKSUM = "file://${COMMON_LICENSE_DIR}/MIT;md5=0835ade698e0bcf8506ecda2f7b4f302"

SRC_URI = " \
    file://label-rootfsb.sh \
    file://label-rootfsb.service \
"

S = "${WORKDIR}"

inherit systemd

RDEPENDS:${PN} = "e2fsprogs-e2fsck e2fsprogs-tune2fs"

SYSTEMD_SERVICE:${PN} = "label-rootfsb.service"

do_install() {
    install -d ${D}${bindir}
    install -d ${D}${systemd_system_unitdir}
    
    install -m 0755 ${WORKDIR}/label-rootfsb.sh ${D}${bindir}/label-rootfsb
    install -m 0644 ${WORKDIR}/label-rootfsb.service ${D}${systemd_system_unitdir}/
}

FILES:${PN} += " \
    ${bindir}/label-rootfsb \
    ${systemd_system_unitdir}/label-rootfsb.service \
"

