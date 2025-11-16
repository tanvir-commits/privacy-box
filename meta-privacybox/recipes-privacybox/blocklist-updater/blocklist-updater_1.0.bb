SUMMARY = "Blocklist Updater - Downloads and updates tracker blocklists"
DESCRIPTION = "Service that downloads EasyList, EasyPrivacy and other blocklists"
LICENSE = "MIT"
LIC_FILES_CHKSUM = "file://${COMMON_LICENSE_DIR}/MIT;md5=0835ade698e0bcf8506ecda2f7b4f302"

SRC_URI = " \
    file://blocklist-updater.py \
    file://blocklist-updater.service \
    file://blocklist-updater.timer \
"

S = "${WORKDIR}"

inherit systemd

RDEPENDS:${PN} = "python3 curl"

SYSTEMD_SERVICE:${PN} = "blocklist-updater.service"
SYSTEMD_AUTO_ENABLE:${PN} = "enable"

do_install() {
    install -d ${D}${bindir}
    install -d ${D}${sysconfdir}/privacy-box
    install -d ${D}${systemd_system_unitdir}
    
    # Install Python script
    install -m 0755 ${WORKDIR}/blocklist-updater.py ${D}${bindir}/blocklist-updater
    
    # Install systemd service and timer (timers go in same directory as services)
    install -m 0644 ${WORKDIR}/blocklist-updater.service ${D}${systemd_system_unitdir}/
    install -m 0644 ${WORKDIR}/blocklist-updater.timer ${D}${systemd_system_unitdir}/
}

FILES:${PN} += " \
    ${sysconfdir}/privacy-box \
    ${systemd_system_unitdir}/blocklist-updater.timer \
"

