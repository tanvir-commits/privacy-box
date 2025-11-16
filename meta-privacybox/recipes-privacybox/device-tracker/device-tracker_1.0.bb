SUMMARY = "Device Tracker - Per-device DNS query attribution"
DESCRIPTION = "Service that correlates DNS queries with devices using DHCP leases"
LICENSE = "MIT"
LIC_FILES_CHKSUM = "file://${COMMON_LICENSE_DIR}/MIT;md5=0835ade698e0bcf8506ecda2f7b4f302"

SRC_URI = " \
    file://device-tracker.py \
    file://device-tracker.service \
    file://requirements.txt \
"

S = "${WORKDIR}"

inherit systemd

RDEPENDS:${PN} = " \
    python3 \
    python3-sqlite3 \
    python3-flask \
    python3-flask-cors \
    dnsmasq \
"

SYSTEMD_SERVICE:${PN} = "device-tracker.service"

do_install() {
    install -d ${D}${bindir}
    install -d ${D}${sysconfdir}/device-tracker
    install -d ${D}${localstatedir}/lib/device-tracker
    install -d ${D}${systemd_system_unitdir}
    
    # Install Python script
    install -m 0755 ${WORKDIR}/device-tracker.py ${D}${bindir}/device-tracker
    
    # Install systemd service
    install -m 0644 ${WORKDIR}/device-tracker.service ${D}${systemd_system_unitdir}/
    
    # Create data directory
    install -d ${D}${localstatedir}/lib/device-tracker
}

FILES:${PN} += " \
    ${sysconfdir}/device-tracker \
    ${localstatedir}/lib/device-tracker \
    ${bindir}/device-tracker \
"

