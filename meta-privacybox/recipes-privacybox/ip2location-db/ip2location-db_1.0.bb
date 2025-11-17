SUMMARY = "IP2Location DB3 Lite Database"
DESCRIPTION = "Free IP geolocation database for country-level lookups"
LICENSE = "MIT"
LIC_FILES_CHKSUM = "file://${COMMON_LICENSE_DIR}/MIT;md5=0835ade698e0bcf8506ecda2f7b4f302"

# Download IP2Location DB3 Lite database during build
# Free database from: https://lite.ip2location.com/database/ip-country
DB_URL = "https://download.ip2location.com/lite/IP2LOCATION-LITE-DB3.BIN"
DB_FILENAME = "IP2LOCATION-LITE-DB3.BIN"

SRC_URI = " \
    ${DB_URL};name=db;downloadfilename=${DB_FILENAME} \
"

SRC_URI[db.sha256sum] = ""  # Skip checksum - database updates frequently
SRC_URI[db.md5sum] = ""     # Skip checksum - database updates frequently

S = "${WORKDIR}"

do_install() {
    install -d ${D}${datadir}/device-tracker
    install -d ${D}${sysconfdir}/device-tracker
    
    # Install database file
    if [ -f "${WORKDIR}/${DB_FILENAME}" ]; then
        install -m 0644 ${WORKDIR}/${DB_FILENAME} ${D}${datadir}/device-tracker/
        install -m 0644 ${WORKDIR}/${DB_FILENAME} ${D}${sysconfdir}/device-tracker/
    else
        bbwarn "IP2Location database file not found. Download may have failed."
    fi
}

FILES:${PN} += " \
    ${datadir}/device-tracker/${DB_FILENAME} \
    ${sysconfdir}/device-tracker/${DB_FILENAME} \
"

