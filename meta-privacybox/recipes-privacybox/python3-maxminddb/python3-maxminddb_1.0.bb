SUMMARY = "MaxMind DB Python Library"
DESCRIPTION = "Python library for reading MaxMind DB files (GeoLite2)"
LICENSE = "Apache-2.0"
LIC_FILES_CHKSUM = "file://${COMMON_LICENSE_DIR}/Apache-2.0;md5=89aea4e17d99a7cacdbeed46a0096b10"

# Install maxminddb via pip at runtime
SRC_URI = " \
    file://install-maxminddb.sh \
    file://maxminddb-install.service \
"

S = "${WORKDIR}"

inherit allarch systemd

SYSTEMD_SERVICE:${PN} = "maxminddb-install.service"

do_install() {
    install -d ${D}${bindir}
    install -d ${D}${systemd_system_unitdir}
    
    install -m 0755 ${WORKDIR}/install-maxminddb.sh ${D}${bindir}/install-maxminddb
    install -m 0644 ${WORKDIR}/maxminddb-install.service ${D}${systemd_system_unitdir}/
}

FILES:${PN} += " \
    ${bindir}/install-maxminddb \
    ${systemd_system_unitdir}/maxminddb-install.service \
"

RDEPENDS:${PN} = "python3-pip"

