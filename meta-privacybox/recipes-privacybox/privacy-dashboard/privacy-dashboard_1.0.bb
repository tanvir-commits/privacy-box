SUMMARY = "Privacy Dashboard - Web interface for per-device tracking visualization"
DESCRIPTION = "Flask-based web dashboard showing real-time per-device privacy tracking"
LICENSE = "MIT"
LIC_FILES_CHKSUM = "file://${COMMON_LICENSE_DIR}/MIT;md5=0835ade698e0bcf8506ecda2f7b4f302"

SRC_URI = " \
    file://app.py \
    file://privacy-dashboard.service \
    file://requirements.txt \
    file://templates/index.html \
    file://static/style.css \
"

S = "${WORKDIR}"

inherit systemd

RDEPENDS:${PN} = " \
    python3 \
    python3-flask \
    python3-flask-cors \
    python3-sqlite3 \
    python3-json \
"

SYSTEMD_SERVICE:${PN} = "privacy-dashboard.service"

do_install() {
    install -d ${D}${bindir}
    install -d ${D}${sysconfdir}/privacy-dashboard
    install -d ${D}${datadir}/privacy-dashboard/templates
    install -d ${D}${datadir}/privacy-dashboard/static
    install -d ${D}${systemd_system_unitdir}
    
    # Install Flask app
    install -m 0755 ${WORKDIR}/app.py ${D}${bindir}/privacy-dashboard
    
    # Install templates and static files (handle case where they might not exist)
    if [ -d "${WORKDIR}/templates" ] && [ "$(ls -A ${WORKDIR}/templates)" ]; then
        install -m 0644 ${WORKDIR}/templates/* ${D}${datadir}/privacy-dashboard/templates/
    fi
    if [ -d "${WORKDIR}/static" ] && [ "$(ls -A ${WORKDIR}/static)" ]; then
        install -m 0644 ${WORKDIR}/static/* ${D}${datadir}/privacy-dashboard/static/
    fi
    
    # Install systemd service
    install -m 0644 ${WORKDIR}/privacy-dashboard.service ${D}${systemd_system_unitdir}/
}

FILES:${PN} += " \
    ${sysconfdir}/privacy-dashboard \
    ${datadir}/privacy-dashboard \
"

