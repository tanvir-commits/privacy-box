SUMMARY = "IP2Location DB3 Lite Database"
DESCRIPTION = "Free IP geolocation database for country-level lookups"
LICENSE = "MIT"
LIC_FILES_CHKSUM = "file://${COMMON_LICENSE_DIR}/MIT;md5=0835ade698e0bcf8506ecda2f7b4f302"

# Download IP2Location DB3 Lite database at runtime
# Free database from: https://lite.ip2location.com/database/ip-country
# Note: Requires free account registration to download
SRC_URI = " \
    file://download-ip2location-db.sh \
    file://ip2location-download.service \
"

S = "${WORKDIR}"

inherit systemd

SYSTEMD_SERVICE:${PN} = "ip2location-download.service"

do_install() {
    install -d ${D}${bindir}
    install -d ${D}${datadir}/device-tracker
    install -d ${D}${sysconfdir}/device-tracker
    install -d ${D}${systemd_system_unitdir}
    
    # Install download script
    install -m 0755 ${WORKDIR}/download-ip2location-db.sh ${D}${bindir}/download-ip2location-db
    install -m 0644 ${WORKDIR}/ip2location-download.service ${D}${systemd_system_unitdir}/
}

FILES:${PN} += " \
    ${bindir}/download-ip2location-db \
    ${datadir}/device-tracker \
    ${sysconfdir}/device-tracker \
    ${systemd_system_unitdir}/ip2location-download.service \
"

RDEPENDS:${PN} = "wget curl"

