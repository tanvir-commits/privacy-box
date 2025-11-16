SUMMARY = "Ensure fw_env.config is installed for RAUC"
DESCRIPTION = "Verifies fw_env.config exists and is correct for i.MX93 FRDM"
LICENSE = "MIT"
LIC_FILES_CHKSUM = "file://${COMMON_LICENSE_DIR}/MIT;md5=0835ade698e0bcf8506ecda2f7b4f302"

# This recipe ensures fw_env.config is installed even if u-boot-env-config fails
# It also provides a verification script

SRC_URI = " \
    file://verify-env.sh \
    file://init-env.sh \
    file://init-env.service \
"

S = "${WORKDIR}"

inherit systemd

RDEPENDS:${PN} = "u-boot-fw-utils u-boot-env-config"

SYSTEMD_SERVICE:${PN} = "init-env.service"

do_install() {
    install -d ${D}${bindir}
    install -d ${D}${systemd_system_unitdir}
    
    install -m 0755 ${WORKDIR}/verify-env.sh ${D}${bindir}/verify-u-boot-env
    install -m 0755 ${WORKDIR}/init-env.sh ${D}${bindir}/init-u-boot-env
    install -m 0644 ${WORKDIR}/init-env.service ${D}${systemd_system_unitdir}/
}

FILES:${PN} += " \
    ${bindir}/verify-u-boot-env \
    ${bindir}/init-u-boot-env \
    ${systemd_system_unitdir}/init-env.service \
"

