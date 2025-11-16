SUMMARY = "Pi-hole - Network-wide ad blocking via DNS"
DESCRIPTION = "Pi-hole is a DNS sinkhole that protects your devices from unwanted content without installing any client-side software"
HOMEPAGE = "https://pi-hole.net"
LICENSE = "EUPL-1.2"
LIC_FILES_CHKSUM = "file://${COMMON_LICENSE_DIR}/EUPL-1.2;md5=be53ff358438cc4718cc781d846c1e86"

SRC_URI = " \
    git://github.com/pi-hole/pi-hole.git;protocol=https;branch=master \
    file://pihole-FTL.service \
    file://pihole-setup.sh \
"

SRCREV = "${AUTOREV}"
PV = "5.0+git${SRCPV}"

S = "${WORKDIR}/git"

DEPENDS = "dnsmasq lighttpd php sqlite3"

RDEPENDS:${PN} = " \
    dnsmasq \
    lighttpd \
    php \
    php-cgi \
    php-cli \
    php-json \
    php-sqlite3 \
    sqlite3 \
    curl \
    wget \
    iputils \
    netbase \
"

inherit systemd

SYSTEMD_SERVICE:${PN} = "pihole-FTL.service"

do_install() {
    # Install Pi-hole files
    install -d ${D}${sysconfdir}/pihole
    install -d ${D}${sysconfdir}/lighttpd/conf.d
    install -d ${D}${localstatedir}/lib/pihole
    install -d ${D}${localstatedir}/log/pihole
    
    # Install setup script
    install -m 0755 ${WORKDIR}/pihole-setup.sh ${D}${bindir}/pihole-setup
    
    # Install systemd service
    install -d ${D}${systemd_system_unitdir}
    install -m 0644 ${WORKDIR}/pihole-FTL.service ${D}${systemd_system_unitdir}/
}

FILES:${PN} += " \
    ${sysconfdir}/pihole \
    ${localstatedir}/lib/pihole \
    ${localstatedir}/log/pihole \
"


